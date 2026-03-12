import os
import uuid
from typing import List, Optional
from datetime import datetime
from app.models.schemas import Meeting, MeetingBase
from app.repositories.interfaces import IMeetingRepository
from app.services.audio_service import AudioProcessingService

class MeetingService:
    def __init__(self, meeting_repo: IMeetingRepository):
        self.meeting_repo = meeting_repo
        self.audio_service = AudioProcessingService()

    def get_all_meetings(self) -> List[Meeting]:
        return self.meeting_repo.get_all()

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        return self.meeting_repo.get_by_id(meeting_id)

    def upload_audio_and_process(self, filename: str,  title: str) -> Meeting:
        # Simulated start
        new_meeting = Meeting(
            id=str(uuid.uuid4()),
            title=title or filename,
            participants=1,
            date=datetime.now().strftime("%d Thg %m, %Y"),
            duration="0m 0s",
            status="ĐANG XỬ LÝ",
            transcript=None
        )
        return self.meeting_repo.create(new_meeting)

    def process_ai_summary(self, meeting_id: str, saved_file_path: str):
        print(f"[MeetingService] Bắt đầu xử lý nền cho cuộc họp {meeting_id}")
        
        # 1. Trích xuất âm thanh nếu là file Video
        video_url = None
        import shutil
        if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
             # Move video to uploads/videos
             os.makedirs("uploads/videos", exist_ok=True)
             filename = os.path.basename(saved_file_path)
             # Strip prefix 'raw_{id}_' if needed, or keep it. Let's keep it for uniqueness.
             persistent_video_path = os.path.join("uploads", "videos", filename)
             shutil.copy2(saved_file_path, persistent_video_path)
             video_url = f"/uploads/videos/{filename}"

             audio_path = self.audio_service.extract_audio(saved_file_path)
             if audio_path:
                 print(f"[MeetingService] Đã trích xuất và lưu audio tại {audio_path}")
                 # Convert filename to public URL
                 audio_filename = os.path.basename(audio_path)
                 persistent_audio_path = os.path.join("uploads", audio_filename)
                 shutil.copy2(audio_path, persistent_audio_path)
                 audio_url = f"/uploads/{audio_filename}"
                 
                 # Cleanup temp audio
                 if os.path.exists(audio_path):
                     os.remove(audio_path)
             else:
                 audio_url = None
        else:
             # Nếu là audio, ta copy nó sang uploads
             filename = os.path.basename(saved_file_path)
             persistent_audio_path = os.path.join("uploads", filename)
             shutil.copy2(saved_file_path, persistent_audio_path)
             audio_url = f"/uploads/{filename}"
             
        # Cleanup original uploaded file (in temp folder)
        if os.path.exists(saved_file_path):
             os.remove(saved_file_path)

        # 2. Mock background LLM completion
        from app.models.models import MeetingDecision
        decision_objs = [MeetingDecision(content=d) for d in ["Approve budget", "Hire new dev"]]
        
        updates = {
            "status": "HOÀN THÀNH",
            "duration": "10m 5s",
            "transcript": "Hello, let's start the meeting...",
            "summary": "This is an auto-generated AI summary after processing the media file.",
            "decisions": decision_objs,
            "audio_url": audio_url,
            "video_url": video_url
        }
        self.meeting_repo.update(meeting_id, updates)
        print(f"[MeetingService] Hoàn tất quá trình AI cho cuộc họp {meeting_id}")

