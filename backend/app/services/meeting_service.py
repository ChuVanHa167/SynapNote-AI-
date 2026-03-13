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

    def upload_audio_and_process(self, filename: str, title: str, duration: Optional[str] = None) -> Meeting:
        # Simulated start
        new_meeting = Meeting(
            id=str(uuid.uuid4()),
            title=title or filename,
            participants=1,
            date=datetime.now().strftime("%d Thg %m, %Y"),
            duration=duration or "0m 0s",
            status="ĐANG XỬ LÝ",
            transcript=None
        )
        return self.meeting_repo.create(new_meeting)

    def process_ai_summary(self, meeting_id: str, saved_file_path: str):
        print(f"[MeetingService] Bắt đầu xử lý nền cho cuộc họp {meeting_id}")
        
        try:
            # 1. Trích xuất âm thanh nếu là file Video (chỉ trích xuất, không cần move video vì đã move ở router)
            audio_url = None
            if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                 print(f"[MeetingService] Đang trích xuất audio từ video...")
                 try:
                     extracted_audio_path = self.audio_service.extract_audio(saved_file_path)
                     if extracted_audio_path:
                         # Move extracted audio to public uploads
                         import shutil
                         audio_filename = os.path.basename(extracted_audio_path)
                         persistent_audio_path = os.path.join("uploads", audio_filename)
                         shutil.copy2(extracted_audio_path, persistent_audio_path)
                         audio_url = f"/uploads/{audio_filename}"
                         
                         # Cleanup temp audio
                         if os.path.exists(extracted_audio_path):
                             os.remove(extracted_audio_path)
                         print(f"[MeetingService] Đã trích xuất audio thành công: {audio_url}")
                 except Exception as ae:
                     print(f"[MeetingService] CẢNH BÁO: Trích xuất audio thất bại: {str(ae)}")
            else:
                 # Nếu là audio, chính nó là audio_url (đã lưu ở router)
                 # Router lưu ở f"/uploads/{persistent_filename}"
                 # Ở đây ta không cần làm gì thêm vì URL đã được set ở router
                 pass

            # 2. Mock background LLM completion
            from app.models.models import MeetingDecision
            decision_objs = [MeetingDecision(content=d) for d in ["Mục tiêu dự án", "Phân công nhiệm vụ"]]
            
            updates = {
                "status": "HOÀN THÀNH",
                "transcript": "Chào mừng bạn đến với buổi họp. Đây là bản dịch mẫu cho nội dung của bạn.",
                "summary": "AI đã phân tích xong. Nội dung chính thảo luận về việc tối ưu hóa quy trình làm việc và triển khai tính năng mới.",
                "decisions": decision_objs
            }
            if audio_url:
                updates["audio_url"] = audio_url

            self.meeting_repo.update(meeting_id, updates)
            print(f"[MeetingService] Đã cập nhật trạng thái HOÀN THÀNH cho {meeting_id}")

        except Exception as e:
            print(f"[MeetingService] LỖI trong background task: {str(e)}")
            self.meeting_repo.update(meeting_id, {
                "status": "LỖI", 
                "summary": f"Lỗi hệ thống trong quá trình xử lý: {str(e)}"
            })

    def delete_meeting(self, meeting_id: str) -> bool:
        return self.meeting_repo.delete(meeting_id)

