import os
import re
import sys
import uuid
import glob
import json
import math
import shutil
import tempfile
import subprocess
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
    """Ensure ffmpeg is available for ffmpeg-python on Windows."""
    if shutil.which("ffmpeg"):
        return True

    candidates: List[str] = []

    # Check imageio_ffmpeg first (pip installed)
    try:
        import imageio_ffmpeg
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_exe and os.path.exists(ffmpeg_exe):
            ffmpeg_dir = os.path.dirname(ffmpeg_exe)
            candidates.append(ffmpeg_dir)
    except Exception:
        pass

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
        if os.path.exists(ffmpeg_exe):
            os.environ["PATH"] = f"{directory}{os.pathsep}{os.environ.get('PATH', '')}"
            break

    return bool(shutil.which("ffmpeg"))


class AIBridgeService:
    """Bridge service that reuses scripts in ai/ for backend workflows."""

    GROQ_MODEL = "whisper-large-v3"
    GEMINI_MODEL = "gemini-flash-lite-latest"
    DEFAULT_CHUNK_SECONDS = 90  # 1.5 minutes - optimal for Vietnamese transcription accuracy

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
            return "He thong chua tim thay ffmpeg de xu ly audio."

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

    # === New: Groq STT + Gemini summary pipeline ===
    def _probe_duration_seconds(self, input_audio_path: str) -> float:
        """Get audio duration using ffmpeg (no ffprobe needed)."""
        try:
            # Use ffmpeg to get duration info from stderr
            result = subprocess.run(
                [self._get_ffmpeg_path(), "-i", input_audio_path],
                capture_output=True,
                text=True,
                check=False,
            )
            output = result.stderr or result.stdout or ""
            
            # Parse Duration: HH:MM:SS.ms from ffmpeg output
            import re
            match = re.search(r"Duration:\s*(\d+):(\d+):(\d+)\.(\d+)", output)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                seconds = int(match.group(3))
                return float(hours * 3600 + minutes * 60 + seconds)
        except Exception as e:
            print(f"[AIBridgeService] Error probing duration: {e}")
        return 0.0
    
    def _get_ffmpeg_path(self) -> str:
        """Get ffmpeg path from imageio_ffmpeg or system."""
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

    def _get_chunk_seconds(self, override: Optional[int] = None) -> int:
        env_val = os.getenv("CHUNK_SECONDS") or os.getenv("CHUNK_SECS")
        try:
            parsed = int(env_val) if env_val is not None else None
        except ValueError:
            parsed = None
        effective = override or parsed or self.DEFAULT_CHUNK_SECONDS
        return max(30, effective)  # clamp to minimum 30s to avoid too many calls

    def _chunk_audio(self, input_audio_path: str, chunk_seconds: int) -> List[str]:
        """Split audio into chunks using ffmpeg subprocess."""
        duration = self._probe_duration_seconds(input_audio_path)
        if duration <= 0:
            raise RuntimeError("Cannot read audio duration for chunking")

        chunk_dir = tempfile.mkdtemp(prefix="sn_chunk_")
        chunks: List[str] = []
        ffmpeg_path = self._get_ffmpeg_path()

        start = 0.0
        idx = 0
        while start < duration:
            out_path = os.path.join(chunk_dir, f"chunk_{idx:04d}.mp3")
            clip_length = min(chunk_seconds, duration - start)
            
            cmd = [
                ffmpeg_path,
                "-i", input_audio_path,
                "-ss", str(start),
                "-t", str(clip_length),
                "-vn",
                "-acodec", "libmp3lame",
                "-ar", "16000",
                "-ac", "1",
                "-loglevel", "error",
                "-y",
                out_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[AIBridgeService] Chunk {idx} failed: {result.stderr}")
                break
                
            chunks.append(out_path)
            start += clip_length
            idx += 1

        return chunks

    def _transcribe_with_groq(self, audio_path: str) -> str:
        groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("Groq_api_key")
        if not groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY")

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError("requests not installed for Groq call") from exc

        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        with open(audio_path, "rb") as f:
            files = {"file": (os.path.basename(audio_path), f, "audio/mpeg")}
            data = {
                "model": self.GROQ_MODEL,
                "response_format": "text",
                "language": "vi",  # Vietnamese language for better accuracy
            }
            headers = {"Authorization": f"Bearer {groq_api_key}"}
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Groq STT failed: {resp.status_code} {resp.text}")
        return resp.text.strip()

    def _summarize_with_gemini(self, transcript: str) -> Dict[str, Any]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
        if not api_key:
            raise RuntimeError("Missing GEMINI_API_KEY")

        default_result = {
            "summary": "Chua the tao tom tat tu dong.",
            "decisions": [],
            "action_items": [],
        }

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError("requests not installed for Gemini call") from exc

        schema_hint = (
            "Tra ve JSON dung schema: {"  # noqa: E501
            "\"summary\": string <=200 tu, "
            "\"decisions\": [string], "
            "\"action_items\": [{\"task\": string, \"assignee\": string, \"deadline\": string, \"status\": string}]"
            "}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": (
                                "Bạn là trợ lý AI. Hãy tóm tắt nội dung cuộc họp dưới 200 từ, "
                                "liệt kê quyết định chính và hành động tiếp theo (nếu có). "
                                "Chi trả về JSON đúng schema, không thêm văn bản thừa.\n"
                                f"{schema_hint}\n\nTranscript:\n{transcript}"
                            )
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json"
            },
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.GEMINI_MODEL}:generateContent?key={api_key}"
        resp = requests.post(url, json=payload, timeout=60)
        if resp.status_code != 200:
            raise RuntimeError(f"Gemini summary failed: {resp.status_code} {resp.text}")

        data = resp.json()
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            parsed = json.loads(text)
            return {
                "summary": parsed.get("summary") or default_result["summary"],
                "decisions": parsed.get("decisions") or [],
                "action_items": parsed.get("action_items") or [],
            }
        except Exception:
            return default_result

    def _fix_transcript_with_gemini(self, transcript: str) -> str:
        """Use Gemini to fix Vietnamese diacritics and punctuation in transcript."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
        if not api_key:
            return transcript  # Fallback to original if no API key

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError("requests not installed for Gemini call") from exc

        # Only fix if transcript is reasonably long (save API calls)
        if len(transcript) < 50:
            return transcript

        prompt = (
            "Bạn là công cụ xử lý văn bản tiếng Việt. "
            "Nhiệm vụ: Sửa lỗi chính tả, thêm dấu câu, và phục hồi dấu tiếng Việt bị mất. "
            "GIỮ NGUYÊN nội dung, không tóm tắt, không thêm bớt thông tin. "
            "Chỉ trả về văn bản đã sửa, không giải thích.\n\n"
            f"Văn bản cần sửa:\n{transcript[:3000]}"  # Limit to avoid token limits
        )

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,  # Low temp for conservative fixes
                "maxOutputTokens": 2048,
            }
        }

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.GEMINI_MODEL}:generateContent?key={api_key}"
        resp = requests.post(url, json=payload, timeout=60)

        if resp.status_code == 200:
            data = resp.json()
            fixed_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
            return fixed_text if fixed_text else transcript
        return transcript  # Fallback on error

    def process_audio_groq_gemini(self, input_audio_path: str, chunk_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Automated pipeline:
        1) Split audio into fixed-size chunks (default 90 seconds)
        2) Send each chunk to Groq Whisper for transcript (with language=vi)
        3) Fix transcript with Gemini (restore diacritics, punctuation)
        4) Send to Gemini for summary
        """

        effective_chunk = self._get_chunk_seconds(chunk_seconds)
        chunks: List[str] = []
        combined_transcript: List[str] = []

        try:
            chunks = self._chunk_audio(input_audio_path, effective_chunk)
            for path in chunks:
                text = self._transcribe_with_groq(path)
                if text:
                    combined_transcript.append(text)

            full_transcript = "\n".join(combined_transcript).strip()

            # Step 3: Fix transcript with Gemini
            if full_transcript:
                full_transcript = self._fix_transcript_with_gemini(full_transcript)

            summary_payload = self._summarize_with_gemini(full_transcript) if full_transcript else {
                "summary": "",
                "decisions": [],
                "action_items": [],
            }

            return {
                "transcript": full_transcript,
                "summary": summary_payload.get("summary") or "",
                "decisions": summary_payload.get("decisions") or [],
                "action_items": summary_payload.get("action_items") or [],
            }
        finally:
            for path in chunks:
                try:
                    os.remove(path)
                except OSError:
                    pass

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