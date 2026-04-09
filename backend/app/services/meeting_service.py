import os
import uuid
import re
import threading
from typing import List, Optional
from datetime import datetime
from app.models.schemas import Meeting, MeetingBase
from app.repositories.interfaces import IMeetingRepository
from app.services.audio_service import AudioProcessingService
from app.services.ai_bridge_service import AIBridgeService

class MeetingService:
    _cancel_lock = threading.Lock()
    _cancel_requested_ids = set()

    def __init__(self, meeting_repo: IMeetingRepository):
        self.meeting_repo = meeting_repo
        self.audio_service = AudioProcessingService()
        self.ai_bridge_service = AIBridgeService()

    @classmethod
    def request_cancel(cls, meeting_id: str) -> None:
        with cls._cancel_lock:
            cls._cancel_requested_ids.add(meeting_id)

    @classmethod
    def clear_cancel(cls, meeting_id: str) -> None:
        with cls._cancel_lock:
            cls._cancel_requested_ids.discard(meeting_id)

    @classmethod
    def is_cancel_requested(cls, meeting_id: str) -> bool:
        with cls._cancel_lock:
            return meeting_id in cls._cancel_requested_ids

    def get_all_meetings(self) -> List[Meeting]:
        return self.meeting_repo.get_all()

    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        return self.meeting_repo.get_by_id(meeting_id)

    def upload_audio_and_process(self, filename: str, title: str, duration: Optional[str] = None, audio_url: Optional[str] = None, video_url: Optional[str] = None) -> Meeting:
        # Auto-detect duration if not provided
        if not duration:
            file_path = audio_url.lstrip('/') if audio_url else filename
            if os.path.exists(file_path):
                duration = self.audio_service.get_duration(file_path)
                print(f"[MeetingService] Auto-detected duration: {duration}")

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

    @staticmethod
    def _duration_to_minutes(duration: Optional[str]) -> float:
        if not duration:
            return 0.0
        value = duration.lower()
        m = re.search(r"(\d+)\s*m", value)
        s = re.search(r"(\d+)\s*s", value)
        minutes = int(m.group(1)) if m else 0
        seconds = int(s.group(1)) if s else 0
        return minutes + seconds / 60.0

    def _resolve_stt_profile(self, requested_profile: Optional[str], duration: Optional[str]) -> str:
        profile = (requested_profile or "auto").strip().lower()
        if profile in {"fast", "balanced", "accurate"}:
            return profile
        if self._duration_to_minutes(duration) <= 10:
            return "accurate"
        return "balanced"

    def process_ai_summary(self, meeting_id: str, saved_file_path: str, stt_profile: str = "auto", duration: Optional[str] = None):
        print(f"[MeetingService] Starting background processing for meeting {meeting_id}")
        if self.is_cancel_requested(meeting_id):
            print(f"[MeetingService] Canceling early processing for meeting {meeting_id}")
            self.meeting_repo.update(meeting_id, {
                "status": "LỖI",
                "summary": "Processing stopped by user request.",
            })
            self.clear_cancel(meeting_id)
            return

        selected_profile = self._resolve_stt_profile(stt_profile, duration)
        print(f"[MeetingService] STT profile: {selected_profile}")
        
        audio_url = None
        persistent_audio_path = None

        try:
            # 1. Trích xuất âm thanh nếu là file Video
            if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                print(f"[MeetingService] Extracting audio from video...")
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
                        print(f"[MeetingService] Successfully extracted audio: {audio_url}")
                except Exception as ae:
                    print(f"[MeetingService] WARNING: Audio separation error: {str(ae)}")
            
            # 2. Thực hiện trích xuất STT + Tóm tắt
            print(f"[MeetingService] Performing Speech-to-Text for {meeting_id}...")
            process_path = persistent_audio_path if (audio_url and os.path.exists(persistent_audio_path)) else saved_file_path
            use_groq_gemini = os.getenv("USE_GROQ_GEMINI", "true").lower() in {"1", "true", "yes"}

            try:
                if use_groq_gemini:
                    try:
                        ai_output = self.ai_bridge_service.process_audio_groq_gemini(process_path)
                        transcript_text = ai_output.get("transcript") or ""
                        print(f"[MeetingService] STT (Groq) completed for {meeting_id}")
                    except Exception as groq_exc:
                        print(f"[MeetingService] Groq pipeline failed, falling back to local STT: {str(groq_exc)}")
                        ai_output = self.ai_bridge_service.process_audio_file(process_path, profile=selected_profile)
                        transcript_text = ai_output.get("transcript") or ""
                        print(f"[MeetingService] STT (fallback) completed for {meeting_id}")
                else:
                    ai_output = self.ai_bridge_service.process_audio_file(process_path, profile=selected_profile)
                    transcript_text = ai_output.get("transcript") or ""
                    print(f"[MeetingService] STT completed for {meeting_id}")
            except Exception as stte:
                print(f"[MeetingService] ERROR: STT failed: {str(stte)}")
                transcript_text = "Unable to extract transcript from audio."
                ai_output = {
                    "summary": "Unable to process AI content for this meeting.",
                    "decisions": [],
                    "action_items": [],
                }

            if self.is_cancel_requested(meeting_id):
                print(f"[MeetingService] Received cancel request for meeting {meeting_id}")
                self.meeting_repo.update(meeting_id, {
                    "status": "LỖI",
                    "summary": "Processing stopped by user request.",
                })
                self.clear_cancel(meeting_id)
                return

            # 3. AI Summary
            updates = {
                "status": "HOÀN THÀNH",
                "transcript": transcript_text,
                "summary": ai_output.get("summary") or "Ban dich da duoc trich xuat thanh cong tu recording.",
                "decisions": ai_output.get("decisions") or [],
                "action_items": ai_output.get("action_items") or [],
            }
            
            if audio_url:
                updates["audio_url"] = audio_url
                # Auto-cleanup video
                if saved_file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                    print(f"[MeetingService] Deleting original video file: {saved_file_path}")
                    try:
                        if os.path.exists(saved_file_path):
                            os.remove(saved_file_path)
                            updates["video_url"] = None
                    except Exception as de:
                        print(f"[MeetingService] CẢNH BÁO: Không thể xóa video: {str(de)}")
            
            self.meeting_repo.update(meeting_id, updates)
            print(f"[MeetingService] Đã cập nhật trạng thái HOÀN THÀNH cho {meeting_id}")
            self.clear_cancel(meeting_id)

        except Exception as e:
            print(f"[MeetingService] LỖI trong background task: {str(e)}")
            self.meeting_repo.update(meeting_id, {
                "status": "LỖI", 
                "summary": f"Lỗi hệ thống: {str(e)}"
            })
            self.clear_cancel(meeting_id)

    def regenerate_summary_sections(self, meeting_id: str) -> Optional[Meeting]:
        meeting = self.meeting_repo.get_by_id(meeting_id)
        if not meeting:
            return None

        transcript_text = (meeting.transcript or "").strip()
        if not transcript_text:
            raise ValueError("Chưa có bản dịch để tạo lại tóm tắt")

        summary_payload = self.ai_bridge_service.summarize_transcript(transcript_text)

        decisions = [str(x).strip() for x in (summary_payload.get("key_points") or []) if str(x).strip()]
        action_items = summary_payload.get("action_items") or []

        normalized_action_items = []
        for item in action_items:
            if isinstance(item, str):
                normalized_action_items.append(
                    {
                        "id": str(uuid.uuid4()),
                        "task": item.strip(),
                        "assignee": "",
                        "deadline": "",
                        "status": "pending",
                    }
                )
            elif isinstance(item, dict):
                task_text = str(item.get("task") or "").strip()
                if not task_text:
                    continue
                normalized_action_items.append(
                    {
                        "id": str(item.get("id") or uuid.uuid4()),
                        "task": task_text,
                        "assignee": str(item.get("assignee") or ""),
                        "deadline": str(item.get("deadline") or ""),
                        "status": str(item.get("status") or "pending"),
                    }
                )

        updates = {
            "summary": summary_payload.get("summary") or "Chua the tao tom tat tu dong.",
            "decisions": decisions,
            "action_items": normalized_action_items,
        }

        return self.meeting_repo.update(meeting_id, updates)

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
