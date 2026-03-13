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

            # 2. Mock transcript based on user's new requirements
            transcript_text = """[00:00 - 00:05]
[Chủ trì]: Chào mừng mọi người đã tham gia buổi họp ngày hôm nay.

[00:06 - 00:15]
[Chủ trì]: Hôm nay chúng ta sẽ xem xét tiến độ dự án SynapNote AI.

[00:16 - 00:25]
[Kỹ thuật]: Hiện tại phần upload file đã hoạt động ổn định với cơ chế robust-save mới.

[00:26 - 00:40]
[Sản phẩm]: Rất tốt. Tiếp theo chúng ta cần tập trung vào hoàn thiện phần giao diện bản dịch.

[00:41 - 00:55]
[AI]: Hệ thống sẽ tự động đồng bộ nội dung và thời gian để người dùng dễ dàng theo sát."""
            
            from app.models.models import MeetingDecision
            decision_objs = [MeetingDecision(content=d) for d in ["Tối ưu hóa upload", "Đồng bộ transcript", "Thêm tính năng Chat AI"]]
            
            updates = {
                "status": "HOÀN THÀNH",
                "transcript": transcript_text,
                "summary": "Buổi họp tập trung vào việc báo cáo tiến độ kỹ thuật và định hướng phát triển giao diện bản dịch đồng bộ.",
                "decisions": decision_objs
            }
            if audio_url:
                updates["audio_url"] = audio_url

            self.meeting_repo.update(meeting_id, updates)
            print(f"[MeetingService] Đã cập nhật trạng thái HOÀN THÀNH với bản dịch Text có Timestamp cho {meeting_id}")

        except Exception as e:
            print(f"[MeetingService] LỖI trong background task: {str(e)}")
            self.meeting_repo.update(meeting_id, {
                "status": "LỖI", 
                "summary": f"Lỗi hệ thống trong quá trình xử lý: {str(e)}"
            })

    def delete_meeting(self, meeting_id: str) -> bool:
        return self.meeting_repo.delete(meeting_id)

