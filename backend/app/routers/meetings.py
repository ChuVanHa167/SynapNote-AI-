import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, File, UploadFile, BackgroundTasks, Depends, Form
from sqlalchemy.orm import Session
from app.models.schemas import Meeting
from app.services.meeting_service import MeetingService
from app.repositories.sql_repos import SqlMeetingRepository
from app.database import get_db

router = APIRouter(prefix="/meetings", tags=["meetings"])

def get_meeting_service(db: Session = Depends(get_db)):
    repo = SqlMeetingRepository(db)
    return MeetingService(repo)

@router.get("/", response_model=List[Meeting])
async def list_meetings(service: MeetingService = Depends(get_meeting_service)):
    return service.get_all_meetings()

@router.get("/{meeting_id}", response_model=Meeting)
async def get_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    return service.get_meeting(meeting_id)

def run_background_processing(meeting_id: str, file_path: str, stt_profile: str = "auto", duration: Optional[str] = None):
    # This runs in a background thread and needs its own DB session
    from app.database import SessionLocal
    from app.repositories.sql_repos import SqlMeetingRepository
    
    db = SessionLocal()
    try:
        repo = SqlMeetingRepository(db)
        service = MeetingService(repo)
        service.process_ai_summary(meeting_id, file_path, stt_profile=stt_profile, duration=duration)
    finally:
        db.close()

@router.post("/upload", response_model=Meeting)
async def upload_audio(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    title: Optional[str] = Form(None), 
    duration: Optional[str] = Form(None),
    stt_profile: Optional[str] = Form("auto"),
    service: MeetingService = Depends(get_meeting_service)
):
    # 1. Start meeting in PENDING status
    new_meeting = service.upload_audio_and_process(file.filename, title, duration)
    MeetingService.clear_cancel(new_meeting.id)
    
    # 2. Determine paths early (Persistent storage)
    is_video = file.filename.lower().endswith(('.mp4', '.mov', '.avi', '.mkv'))
    persistent_dir = "uploads/videos" if is_video else "uploads/audio"
    os.makedirs(persistent_dir, exist_ok=True)
    
    persistent_filename = f"raw_{new_meeting.id}_{file.filename}"
    persistent_path = os.path.join(persistent_dir, persistent_filename)
    public_url = f"/{persistent_dir}/{persistent_filename}"
    
    # 3. Save physical file directly to persistent storage (Optimized streaming)
    print(f"[Upload] Đang lưu file (Streaming): {file.filename}")
    try:
        with open(persistent_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        actual_size = os.path.getsize(persistent_path)
        print(f"[Upload] Đã lưu xong (Streaming). Kích thước: {actual_size} bytes")
             
    except Exception as e:
        print(f"[Upload] LỖI khi lưu file: {str(e)}")
    
    # 4. Update DB with URL immediately so it's playable
    if is_video:
        service.meeting_repo.update(new_meeting.id, {"video_url": public_url})
    else:
        service.meeting_repo.update(new_meeting.id, {"audio_url": public_url})

    # 5. Start background AI processing (using the persistent path)
    background_tasks.add_task(
        run_background_processing,
        new_meeting.id,
        persistent_path,
        stt_profile or "auto",
        duration,
    )
    
    return service.get_meeting(new_meeting.id)

@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str, service: MeetingService = Depends(get_meeting_service)):
    if not service.delete_meeting(meeting_id):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting deleted successfully"}

@router.post("/{meeting_id}/reprocess", response_model=Meeting)
async def reprocess_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    stt_profile: Optional[str] = "auto",
    service: MeetingService = Depends(get_meeting_service)
):
    # 1. Check if meeting exists
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # 2. Update status to PENDING/PROCESSING
    MeetingService.clear_cancel(meeting_id)
    service.meeting_repo.update(meeting_id, {"status": "ĐANG XỬ LÝ"})
    
    # 3. Identify path for processing
    # We prefer extracted audio if it exists, otherwise video
    # Note: Logic in process_ai_summary handles this, so we just need a valid path
    import os
    is_video = meeting.video_url is not None
    persistent_dir = "uploads/videos" if is_video else "uploads/audio"
    filename = os.path.basename(meeting.video_url or meeting.audio_url)
    persistent_path = os.path.join(persistent_dir, filename)
    
    # 4. Trigger background task
    background_tasks.add_task(
        run_background_processing,
        meeting_id,
        persistent_path,
        stt_profile or "auto",
        meeting.duration,
    )
    
    return service.get_meeting(meeting_id)


@router.post("/{meeting_id}/stop", response_model=Meeting)
async def stop_processing(
    meeting_id: str,
    service: MeetingService = Depends(get_meeting_service),
):
    meeting = service.get_meeting(meeting_id)
    if not meeting:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Meeting not found")

    MeetingService.request_cancel(meeting_id)
    service.meeting_repo.update(
        meeting_id,
        {
            "status": "LỖI",
            "summary": "Da dung ban dich theo yeu cau nguoi dung.",
        },
    )
    return service.get_meeting(meeting_id)
