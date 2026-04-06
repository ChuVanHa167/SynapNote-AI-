import uuid
import time
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from threading import Lock

@dataclass
class JobProgress:
    """Track progress of a file upload/download job"""
    job_id: str
    status: str = "pending"  # pending, downloading, uploading, processing, completed, error
    progress: float = 0.0  # 0-100
    message: str = ""
    total_bytes: int = 0
    downloaded_bytes: int = 0
    uploaded_bytes: int = 0
    file_url: Optional[str] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    
    # Callbacks for SSE
    _listeners: list = field(default_factory=list, repr=False)
    _lock: Lock = field(default_factory=Lock, repr=False)

class JobTracker:
    """Singleton job tracker for upload/download progress"""
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobTracker, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if JobTracker._initialized:
            return
        self._jobs: Dict[str, JobProgress] = {}
        self._lock = Lock()
        JobTracker._initialized = True
    
    def create_job(self, job_id: Optional[str] = None) -> JobProgress:
        """Create a new job and return it"""
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        with self._lock:
            job = JobProgress(job_id=job_id)
            self._jobs[job_id] = job
            return job
    
    def get_job(self, job_id: str) -> Optional[JobProgress]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def update_progress(self, job_id: str, progress: float, message: str = "", status: Optional[str] = None):
        """Update job progress"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.progress = min(100.0, max(0.0, progress))
                if message:
                    job.message = message
                if status:
                    job.status = status
                job.updated_at = time.time()
                # Notify listeners
                for listener in job._listeners:
                    try:
                        listener(job)
                    except Exception:
                        pass
    
    def update_bytes(self, job_id: str, downloaded: int = 0, uploaded: int = 0, total: int = 0):
        """Update byte counters and calculate progress"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                if total > 0:
                    job.total_bytes = total
                if downloaded > 0:
                    job.downloaded_bytes = downloaded
                if uploaded > 0:
                    job.uploaded_bytes = uploaded
                
                # Calculate progress
                if job.total_bytes > 0:
                    if job.status == "downloading":
                        job.progress = (job.downloaded_bytes / job.total_bytes) * 100
                    elif job.status == "uploading":
                        job.progress = (job.uploaded_bytes / job.total_bytes) * 100
                
                job.updated_at = time.time()
    
    def set_error(self, job_id: str, error: str):
        """Set job error status"""
        self.update_progress(job_id, 0, error, "error")
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.error = error
    
    def complete_job(self, job_id: str, file_url: str):
        """Mark job as completed"""
        self.update_progress(job_id, 100, "Hoàn thành", "completed")
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.file_url = file_url
    
    def add_listener(self, job_id: str, callback: Callable[[JobProgress], None]):
        """Add progress listener for SSE"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                with job._lock:
                    job._listeners.append(callback)
    
    def remove_listener(self, job_id: str, callback: Callable[[JobProgress], None]):
        """Remove progress listener"""
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                with job._lock:
                    if callback in job._listeners:
                        job._listeners.remove(callback)
    
    def cleanup_old_jobs(self, max_age_seconds: float = 3600):
        """Remove jobs older than max_age_seconds"""
        current_time = time.time()
        with self._lock:
            to_remove = [
                job_id for job_id, job in self._jobs.items()
                if current_time - job.created_at > max_age_seconds
            ]
            for job_id in to_remove:
                del self._jobs[job_id]

# Singleton instance
job_tracker = JobTracker()
