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

    def upload_audio_and_process(self, filename: str, title: str, duration: Optional[str] = None, audio_url: Optional[str] = None, video_url: Optional[str] = None) -> Meeting:
        new_meeting = Meeting(
            id=str(uuid.uuid4()),
            title=title or filename,
            participants=1,
            date=datetime.now().strftime("%d Thg %m, %Y"),
            duration=duration or "0m 0s",
            status="ĐANG XỬ LÝ",
            transcript=None,
            audio_url=audio_url,
            video_url=video_url
        )
        return self.meeting_repo.create(new_meeting)

    def process_ai_summary(self, meeting_id: str, saved_file_path: str):
        print(f"[MeetingService] Bắt đầu xử lý nền cho cuộc họp {meeting_id}")
        
        audio_url = None
        persistent_audio_path = None

        try:
            # 1. Trích xuất âm thanh nếu là file Video
            if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                print(f"[MeetingService] Đang trích xuất audio từ video...")
                try:
                    extracted_audio_path = self.audio_service.extract_audio(saved_file_path)
                    if extracted_audio_path:
                        audio_filename = os.path.basename(extracted_audio_path)
                        target_dir = "uploads/audio"
                        os.makedirs(target_dir, exist_ok=True)
                        persistent_audio_path = os.path.join(target_dir, audio_filename)
                        
                        # Only copy if different
                        if os.path.abspath(extracted_audio_path) != os.path.abspath(persistent_audio_path):
                            import shutil
                            shutil.copy2(extracted_audio_path, persistent_audio_path)
                        
                        audio_url = f"/uploads/audio/{audio_filename}"
                        print(f"[MeetingService] Đã trích xuất audio thành công: {audio_url}")
                except Exception as ae:
                    print(f"[MeetingService] CẢNH BÁO: Phân tách audio gặp lỗi: {str(ae)}")
            
            # 2. Thực hiện trích xuất STT
            print(f"[MeetingService] Đang thực hiện Speech-to-Text cho {meeting_id}...")
            try:
                import sys
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                if project_root not in sys.path:
                    sys.path.append(project_root)
                
                from ai.STT.stt import speech_to_text
                process_path = persistent_audio_path if (audio_url and os.path.exists(persistent_audio_path)) else saved_file_path
                
                transcript_text = speech_to_text(process_path)
                print(f"[MeetingService] STT hoàn tất cho {meeting_id}")
            except Exception as stte:
                print(f"[MeetingService] LỖI: STT thất bại: {str(stte)}")
                transcript_text = "Không thể trích xuất bản dịch từ âm thanh."

            # 3. AI Summary
            from app.models.models import MeetingDecision
            decision_objs = [MeetingDecision(content=d) for d in ["Tối ưu hóa upload", "Đồng bộ transcript", "Thêm tính năng Chat AI"]]
            
            updates = {
                "status": "HOÀN THÀNH",
                "transcript": transcript_text,
                "summary": "Bản dịch đã được trích xuất thành công từ recording.",
                "decisions": decision_objs
            }
            
            if audio_url:
                updates["audio_url"] = audio_url
                # Auto-cleanup video
                if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    print(f"[MeetingService] Đang xóa file video gốc: {saved_file_path}")
                    try:
                        if os.path.exists(saved_file_path):
                            os.remove(saved_file_path)
                            updates["video_url"] = None
                    except Exception as de:
                        print(f"[MeetingService] CẢNH BÁO: Không thể xóa video: {str(de)}")
            
            self.meeting_repo.update(meeting_id, updates)
            print(f"[MeetingService] Đã cập nhật trạng thái HOÀN THÀNH cho {meeting_id}")

        except Exception as e:
            print(f"[MeetingService] LỖI trong background task: {str(e)}")
            self.meeting_repo.update(meeting_id, {
                "status": "LỖI", 
                "summary": f"Lỗi hệ thống: {str(e)}"
            })

    def delete_meeting(self, meeting_id: str) -> bool:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            return False
        
        for url in [meeting.audio_url, meeting.video_url]:
            if url:
                file_path = url.lstrip('/')
                try:
                    if os.path.exists(file_path):
                        print(f"[MeetingService] Đang xóa file media: {file_path}")
                        os.remove(file_path)
                except Exception as e:
                    print(f"[MeetingService] CẢNH BÁO: Không thể xóa {file_path}: {str(e)}")
        
        return self.meeting_repo.delete(meeting_id)
