import os
import re
import sys
import uuid
import glob
import shutil
from typing import Any, Dict, List, Optional

from app.models.schemas import Meeting


STT_PROFILES: Dict[str, Dict[str, Any]] = {
    "fast": {
        "model_size": "small",
        "compute_type": "int8",
        "beam_size": 1,
        "best_of": 1,
        "temperature": 0,
        "vad_filter": True,
        "without_timestamps": False,
        "condition_on_previous_text": False,
    },
    "balanced": {
        "model_size": "medium",
        "compute_type": "int8",
        "beam_size": 3,
        "best_of": 3,
        "temperature": 0,
        "vad_filter": True,
        "condition_on_previous_text": True,
    },
    "accurate": {
        "model_size": "large-v3",
        "compute_type": "int8",
        "beam_size": 5,
        "best_of": 5,
        "temperature": 0,
        "vad_filter": True,
        "condition_on_previous_text": True,
    },
    "ultra": {
        "model_size": "large-v3",
        "compute_type": "float16",
        "beam_size": 8,
        "best_of": 8,
        "temperature": 0,
        "vad_filter": True,
        "condition_on_previous_text": True,
    },
}


def _ensure_project_root_on_path() -> None:
    """Allow backend modules to import the top-level ai package."""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    if project_root not in sys.path:
        sys.path.append(project_root)


def _extract_first_sentences(text: str, limit: int = 3) -> List[str]:
    parts = [p.strip() for p in re.split(r"[.!?]+", text or "") if p.strip()]
    return parts[:limit]


def _ensure_ffmpeg_on_path() -> bool:
    """Ensure ffmpeg and ffprobe are available for ffmpeg-python on Windows."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True

    candidates: List[str] = []

    env_bin = os.getenv("FFMPEG_BIN_DIR")
    if env_bin:
        candidates.append(env_bin)

    localappdata = os.getenv("LOCALAPPDATA", "")
    if localappdata:
        pattern = os.path.join(
            localappdata,
            "Microsoft",
            "WinGet",
            "Packages",
            "Gyan.FFmpeg*",
            "ffmpeg-*-full_build",
            "bin",
        )
        candidates.extend(glob.glob(pattern))

    candidates.append(r"C:\ffmpeg\bin")

    for directory in candidates:
        ffmpeg_exe = os.path.join(directory, "ffmpeg.exe")
        ffprobe_exe = os.path.join(directory, "ffprobe.exe")
        if os.path.exists(ffmpeg_exe) and os.path.exists(ffprobe_exe):
            os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"
            break

    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


class AIBridgeService:
    """Bridge service that reuses scripts in ai/ for backend workflows."""

    @staticmethod
    def normalize_profile(profile: Optional[str]) -> str:
        key = (profile or "balanced").strip().lower()
        if key == "auto":
            key = "balanced"
        return key if key in STT_PROFILES else "balanced"

    def transcribe_audio(self, input_audio_path: str, profile: Optional[str] = "balanced") -> str:
        _ensure_project_root_on_path()
        temp_wav_path: Optional[str] = None
        selected_profile = self.normalize_profile(profile)
        stt_config = STT_PROFILES[selected_profile]

        if not _ensure_ffmpeg_on_path():
            return "He thong chua tim thay ffmpeg/ffprobe de xu ly audio."

        try:
            from ai.stt_test import clean_text, convert_audio, transcribe

            temp_wav_path = convert_audio(input_audio_path)
            raw_text = transcribe(temp_wav_path, profile_config=stt_config)
            return clean_text(raw_text)
        except Exception as exc:
            print(f"[AIBridgeService] STT fallback due to error: {exc}")
            return "Khong the trich xuat transcript tu file audio nay o thoi diem hien tai."
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.remove(temp_wav_path)
                except OSError:
                    pass

    def summarize_transcript(self, transcript_text: str) -> Dict[str, Any]:
        _ensure_project_root_on_path()

        default_result = {
            "summary": "Chua the tao tom tat tu dong.",
            "key_points": [],
            "action_items": [],
            "keywords": [],
        }

        if not transcript_text or not transcript_text.strip():
            return default_result

        try:
            from ai.summary_test import summarize

            result = summarize(transcript_text)
            if isinstance(result, dict):
                return {
                    "summary": result.get("summary") or default_result["summary"],
                    "key_points": result.get("key_points") or [],
                    "action_items": result.get("action_items") or [],
                    "keywords": result.get("keywords") or [],
                }
            return default_result
        except Exception as exc:
            print(f"[AIBridgeService] Summary fallback due to error: {exc}")
            fallback_points = _extract_first_sentences(transcript_text, 3)
            return {
                "summary": " ".join(fallback_points) if fallback_points else default_result["summary"],
                "key_points": fallback_points,
                "action_items": [],
                "keywords": [],
            }

    def process_audio_file(self, input_audio_path: str, profile: Optional[str] = "balanced") -> Dict[str, Any]:
        transcript = self.transcribe_audio(input_audio_path, profile=profile)
        summary_payload = self.summarize_transcript(transcript)

        decisions = summary_payload.get("key_points") or []
        action_items = summary_payload.get("action_items") or []

        normalized_action_items: List[Dict[str, str]] = []
        for item in action_items:
            if isinstance(item, str):
                normalized_action_items.append(
                    {
                        "id": str(uuid.uuid4()),
                        "task": item,
                        "assignee": "",
                        "deadline": "",
                        "status": "pending",
                    }
                )
            elif isinstance(item, dict):
                normalized_action_items.append(
                    {
                        "id": str(item.get("id") or uuid.uuid4()),
                        "task": str(item.get("task") or ""),
                        "assignee": str(item.get("assignee") or ""),
                        "deadline": str(item.get("deadline") or ""),
                        "status": str(item.get("status") or "pending"),
                    }
                )

        return {
            "transcript": transcript,
            "summary": summary_payload.get("summary") or "",
            "decisions": [str(x) for x in decisions if str(x).strip()],
            "action_items": normalized_action_items,
        }

    def answer_question(self, message: str, meeting: Optional[Meeting]) -> str:
        question = (message or "").strip()
        if not question:
            return "Ban hay nhap cau hoi de toi co the ho tro."

        if not meeting:
            return "Khong tim thay cuoc hop phu hop de tra loi cau hoi nay."

        normalized_status = (meeting.status or "").upper()
        is_completed = normalized_status in {"HOAN THANH", "HOÀN THÀNH"}

        if not is_completed and not (meeting.summary or meeting.transcript):
            return "Du lieu AI cua cuoc hop nay chua san sang. Ban hay doi qua trinh xu ly hoan tat."

        summary = (meeting.summary or "").strip()
        transcript = (meeting.transcript or "").strip()

        if any(k in question.lower() for k in ["tom tat", "summary", "tong ket"]):
            if summary:
                return f"Tom tat cuoc hop: {summary}"

        if any(k in question.lower() for k in ["quyet dinh", "decision"]):
            if meeting.decisions:
                listed = "\n".join([f"- {d}" for d in meeting.decisions])
                return f"Cac quyet dinh chinh:\n{listed}"

        if transcript:
            snippet = " ".join(_extract_first_sentences(transcript, 2))
            return (
                "Toi da tim trong transcript va summary cua cuoc hop. "
                f"Thong tin lien quan: {snippet if snippet else summary}"
            )

        if summary:
            return f"Toi da tim trong summary va thay noi dung lien quan: {summary}"

        return "Hien tai chua co du lieu transcript/summary de tra loi chinh xac."