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
        if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
             audio_path = self.audio_service.extract_audio(saved_file_path)
             if audio_path:
                 print(f"[MeetingService] Sẽ gửi {audio_path} cho AI (Whisper) phân tích...")
                 # Clean up extracted audio
                 os.remove(audio_path)
        else:
             print(f"[MeetingService] File là audio, truyền thẳng tới AI (Whisper)...")
             
        # Cleanup original uploaded file
        if os.path.exists(saved_file_path):
             os.remove(saved_file_path)

        # 2. Mock background LLM completion
        updates = {
            "status": "HOÀN THÀNH",
            "duration": "10m 5s",
            "transcript": "Hello, let's start the meeting...",
            "summary": "This is an auto-generated AI summary after processing the media file.",
            "decisions": ["Approve budget", "Hire new dev"]
        }
        self.meeting_repo.update(meeting_id, updates)
        print(f"[MeetingService] Hoàn tất quá trình AI cho cuộc họp {meeting_id}")

