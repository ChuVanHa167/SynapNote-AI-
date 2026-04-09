import os
import re
import sys
import uuid
import glob
import json
import shutil
import tempfile
import subprocess
from typing import Any, Dict, List, Optional

from app.models.schemas import Meeting
from app.services.prompt import (
    get_gemini_diarization_prompt,
    get_gemini_summary_prompt,
    get_gemini_transcript_fix_prompt,
    get_groq_transcription_prompt,
)


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

    GROQ_MODEL = "whisper-large-v3-turbo"
    GEMINI_MODEL = "gemini-flash-lite-latest"
    DEFAULT_CHUNK_SECONDS = 120  # 2 minutes - optimal for Vietnamese transcription accuracy
    MAX_TRANSCRIPT_FIX_CHARS_PER_CALL = 2800
    MAX_TRANSCRIPT_SUMMARY_CHARS = 32000
    MAX_FIX_CHUNKS = 20
    UNWANTED_STT_PATTERNS = (
        re.compile(
            r"Hãy\s+subscribe\s+cho\s+kênh\s+Ghiền\s+Mì\s+Gõ\s+để\s+không\s+bỏ\s+lỡ\s+những\s+video\s+hấp\s+dẫn\.?",
            flags=re.IGNORECASE,
        ),
        re.compile(
            r"Hay\s+subscribe\s+cho\s+kenh\s+Ghien\s+Mi\s+Go\s+de\s+khong\s+bo\s+lo\s+nhung\s+video\s+hap\s+dan\.?",
            flags=re.IGNORECASE,
        ),
    )

    def _sanitize_stt_output(self, text: str) -> str:
        if not text:
            return ""

        cleaned = text
        for pattern in self.UNWANTED_STT_PATTERNS:
            cleaned = pattern.sub("", cleaned)

        # Keep line structure stable while trimming artifacts left after removal.
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        cleaned = re.sub(r" *\n *", "\n", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    def _is_truthy(self, value: Optional[str], default: bool = False) -> bool:
        if value is None:
            return default
        return value.strip().lower() in {"1", "true", "yes", "on"}

    def _is_llm_diarization_enabled(self) -> bool:
        return self._is_truthy(os.getenv("ENABLE_LLM_DIARIZATION"), default=False)

    def _is_gemini_transcript_fix_enabled(self) -> bool:
        # Keep default enabled so Groq output is standardized by Gemini for better readability.
        return self._is_truthy(os.getenv("ENABLE_GEMINI_TRANSCRIPT_FIX"), default=True)

    def _get_diarization_max_input_chars(self) -> int:
        raw = os.getenv("LLM_DIARIZATION_MAX_INPUT_CHARS")
        try:
            parsed = int(raw) if raw else 16000
        except ValueError:
            parsed = 16000
        return max(2000, min(parsed, 40000))

    def _format_seconds(self, seconds: float) -> str:
        total = max(0, int(seconds))
        minutes = total // 60
        secs = total % 60
        return f"{minutes:02d}:{secs:02d}"

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
            return self._sanitize_stt_output(clean_text(raw_text))
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
                encoding="utf-8",
                errors="ignore",
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
        """Get chunk size in seconds. Default increased to 120s for faster processing."""
        env_val = os.getenv("CHUNK_SECONDS") or os.getenv("CHUNK_SECS")
        try:
            parsed = int(env_val) if env_val is not None else None
        except ValueError:
            parsed = None
        # Default changed from 90s to 120s for better performance
        effective = override or parsed or 120
        return max(60, effective)  # clamp to minimum 60s

    def _chunk_audio(self, input_audio_path: str, chunk_seconds: int) -> List[Dict[str, Any]]:
        """Split audio into chunks using ffmpeg subprocess."""
        duration = self._probe_duration_seconds(input_audio_path)
        if duration <= 0:
            raise RuntimeError("Cannot read audio duration for chunking")

        chunk_dir = tempfile.mkdtemp(prefix="sn_chunk_")
        chunks: List[Dict[str, Any]] = []
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
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            if result.returncode != 0:
                print(f"[AIBridgeService] Chunk {idx} failed: {result.stderr}")
                break

            end = start + clip_length
            chunks.append(
                {
                    "path": out_path,
                    "start": float(start),
                    "end": float(end),
                }
            )
            start += clip_length
            idx += 1

        return chunks

    def _transcribe_with_groq(self, audio_path: str, request_id: Optional[str] = None) -> str:
        """Transcribe audio with Groq API.

        Args:
            audio_path: Path to audio file
            request_id: Unique ID to prevent caching (optional)
        """
        groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("Groq_api_key")
        if not groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY")

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError("requests not installed for Groq call") from exc

        url = "https://api.groq.com/openai/v1/audio/transcriptions"

        # Generate unique request ID to prevent API caching
        unique_id = request_id or str(uuid.uuid4())

        with open(audio_path, "rb") as f:
            file_content = f.read()

        # Use unique filename for each request to prevent Groq caching
        unique_filename = f"audio_{unique_id}_{os.path.basename(audio_path)}"
        files = {"file": (unique_filename, file_content, "audio/mpeg")}

        data = {
            "model": self._get_groq_model(),
            "response_format": "text",
            "language": "vi",  # Vietnamese language for better accuracy
            "temperature": 0.0,  # Add temperature to ensure deterministic but fresh results
        }

        # Add unique request ID as prompt to break any cache
        data["prompt"] = get_groq_transcription_prompt(unique_id)

        headers = {
            "Authorization": f"Bearer {groq_api_key}",
            "X-Request-ID": unique_id,  # Add request ID header
        }

        resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)
        if resp.status_code != 200:
            raise RuntimeError(f"Groq STT failed: {resp.status_code} {resp.text}")
        return self._sanitize_stt_output(resp.text.strip())

    def _get_groq_model(self) -> str:
        return os.getenv("GROQ_MODEL", self.GROQ_MODEL)

    def _get_gemini_model(self) -> str:
        return os.getenv("GEMINI_MODEL", self.GEMINI_MODEL)

    def _get_gemini_model_candidates(self) -> List[str]:
        primary = self._get_gemini_model().strip()
        fallback_raw = os.getenv(
            "GEMINI_FALLBACK_MODELS",
            "gemini-flash-lite-latest,gemini-flash-lite-latest",
        )

        models: List[str] = []
        for model in [primary] + [m.strip() for m in fallback_raw.split(",")]:
            if model and model not in models:
                models.append(model)
        return models

    def _extract_json_object(self, raw_text: str) -> Dict[str, Any]:
        if not raw_text:
            return {}

        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            text = re.sub(r"```$", "", text).strip()

        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                parsed = json.loads(text[start : end + 1])
                return parsed if isinstance(parsed, dict) else {}
            except Exception:
                return {}

        return {}

    def _normalize_decisions(self, decisions: Any) -> List[str]:
        if not isinstance(decisions, list):
            return []

        normalized: List[str] = []
        seen = set()

        for item in decisions:
            text = str(item or "").strip()
            if len(text) < 8 or "?" in text:
                continue

            lowered = text.lower()
            if lowered.startswith(("co the", "có thể", "de xuat", "đề xuất", "goi y", "gợi ý")):
                continue

            key = re.sub(r"\s+", " ", lowered)
            if key in seen:
                continue
            seen.add(key)
            normalized.append(text)

        return normalized[:8]

    def _normalize_action_items(self, action_items: Any) -> List[Dict[str, str]]:
        if not isinstance(action_items, list):
            return []

        normalized: List[Dict[str, str]] = []
        seen_tasks = set()

        for item in action_items:
            if isinstance(item, str):
                task = item.strip()
                assignee = ""
                deadline = ""
                status = "pending"
            elif isinstance(item, dict):
                task = str(item.get("task") or "").strip()
                assignee = str(item.get("assignee") or "").strip()
                deadline = str(item.get("deadline") or "").strip()
                status = str(item.get("status") or "pending").strip().lower()
            else:
                continue

            if len(task) < 6:
                continue

            task_key = re.sub(r"\s+", " ", task.lower())
            if task_key in seen_tasks:
                continue
            seen_tasks.add(task_key)

            if status not in {"pending", "in_progress", "completed"}:
                status = "pending"

            normalized.append(
                {
                    "id": str(uuid.uuid4()),
                    "task": task,
                    "assignee": assignee,
                    "deadline": deadline,
                    "status": status,
                }
            )

        return normalized[:12]

    def _split_text_for_fix(self, text: str, max_chars: int) -> List[str]:
        clean = (text or "").strip()
        if not clean:
            return []
        if len(clean) <= max_chars:
            return [clean]

        lines = clean.splitlines()
        chunks: List[str] = []
        current = ""

        for line in lines:
            line = line.rstrip()
            candidate = f"{current}\n{line}".strip() if current else line
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                chunks.append(current)
                current = ""

            if len(line) <= max_chars:
                current = line
            else:
                for i in range(0, len(line), max_chars):
                    piece = line[i : i + max_chars]
                    if len(piece) == max_chars:
                        chunks.append(piece)
                    else:
                        current = piece

        if current:
            chunks.append(current)

        return chunks if chunks else [clean]

    def _truncate_for_summary(self, transcript: str) -> str:
        if len(transcript) <= self.MAX_TRANSCRIPT_SUMMARY_CHARS:
            return transcript

        head = self.MAX_TRANSCRIPT_SUMMARY_CHARS // 2
        tail = self.MAX_TRANSCRIPT_SUMMARY_CHARS - head
        return (
            f"{transcript[:head]}\n\n"
            "[... NOI DUNG O GIUA DA DUOC RUT GON DE VUA GIOI HAN TOKEN ...]\n\n"
            f"{transcript[-tail:]}"
        )

    def _limit_summary_words(self, text: str, max_words: int = 200) -> str:
        words = (text or "").strip().split()
        if not words:
            return ""
        if len(words) <= max_words:
            return " ".join(words)
        return " ".join(words[:max_words])

    def _build_fallback_summary_payload(self, transcript: str) -> Dict[str, Any]:
        fallback_sentences = _extract_first_sentences(transcript, 3)
        fallback_summary = self._limit_summary_words(". ".join(fallback_sentences))
        if not fallback_summary:
            fallback_summary = "Chua the tao tom tat tu dong."

        return {
            "summary": fallback_summary,
            "decisions": [],
            "action_items": [],
        }

    def _normalize_speaker_turns(self, raw_turns: Any, max_end_seconds: float) -> List[Dict[str, Any]]:
        if not isinstance(raw_turns, list):
            return []

        speaker_alias: Dict[str, str] = {}
        normalized: List[Dict[str, Any]] = []

        for item in raw_turns:
            if not isinstance(item, dict):
                continue

            text = str(item.get("text") or "").strip()
            if len(text) < 2:
                continue

            try:
                start = float(item.get("start"))
                end = float(item.get("end"))
            except (TypeError, ValueError):
                continue

            start = max(0.0, start)
            end = max(start + 0.2, end)
            if max_end_seconds > 0:
                start = min(start, max_end_seconds)
                end = min(end, max_end_seconds)
            if end - start < 0.2:
                continue

            raw_speaker = str(item.get("speaker") or "").strip().lower()
            if not raw_speaker:
                raw_speaker = f"unknown_{len(speaker_alias) + 1}"

            if raw_speaker not in speaker_alias:
                speaker_alias[raw_speaker] = f"Speaker {len(speaker_alias) + 1}"

            normalized.append(
                {
                    "speaker": speaker_alias[raw_speaker],
                    "start": round(start, 2),
                    "end": round(end, 2),
                    "text": text,
                }
            )

        if not normalized:
            return []

        normalized.sort(key=lambda turn: turn["start"])

        merged: List[Dict[str, Any]] = [normalized[0].copy()]
        for turn in normalized[1:]:
            last = merged[-1]
            if turn["speaker"] == last["speaker"] and (turn["start"] - last["end"]) <= 1.0:
                last["end"] = max(last["end"], turn["end"])
                last["text"] = f"{last['text']} {turn['text']}".strip()
            else:
                merged.append(turn.copy())

        return merged

    def _build_speaker_transcript(self, speaker_turns: List[Dict[str, Any]]) -> Dict[str, str]:
        if not speaker_turns:
            return {"transcript": "", "summary_source": ""}

        transcript_lines = [
            f"[{turn['speaker']} | {self._format_seconds(turn['start'])}-{self._format_seconds(turn['end'])}] {turn['text']}"
            for turn in speaker_turns
        ]
        summary_lines = [f"{turn['speaker']}: {turn['text']}" for turn in speaker_turns]

        return {
            "transcript": "\n".join(transcript_lines),
            "summary_source": "\n".join(summary_lines),
        }

    def _diarize_with_gemini(self, chunk_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not self._is_llm_diarization_enabled():
            return []

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
        if not api_key:
            return []

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError("requests not installed for Gemini call") from exc

        compact_chunks: List[Dict[str, Any]] = []
        max_chars = self._get_diarization_max_input_chars()
        used_chars = 0

        for index, chunk in enumerate(chunk_items):
            text = str(chunk.get("text") or "").strip()
            if not text:
                continue

            if used_chars >= max_chars:
                break

            remaining = max_chars - used_chars
            excerpt = text[: min(1200, remaining)]
            if not excerpt:
                continue

            compact_chunks.append(
                {
                    "chunk_index": index,
                    "start": round(float(chunk.get("start") or 0.0), 2),
                    "end": round(float(chunk.get("end") or 0.0), 2),
                    "text": excerpt,
                }
            )
            used_chars += len(excerpt)

        if len(compact_chunks) < 2:
            return []

        prompt = get_gemini_diarization_prompt(compact_chunks)

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
                "topP": 0.9,
                "maxOutputTokens": 3072,
            },
        }

        model_name = self._get_gemini_model()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        try:
            resp = requests.post(url, json=payload, timeout=90)
        except Exception as exc:
            print(f"[AIBridgeService] Gemini diarization request failed: {exc}")
            return []

        if resp.status_code != 200:
            print(f"[AIBridgeService] Gemini diarization failed: {resp.status_code} {resp.text[:200]}")
            return []

        try:
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as exc:
            print(f"[AIBridgeService] Gemini diarization parse failed: {exc}")
            return []

        parsed = self._extract_json_object(text)
        max_end = max(float(chunk.get("end") or 0.0) for chunk in compact_chunks)
        return self._normalize_speaker_turns(parsed.get("speaker_turns"), max_end)

    def _summarize_with_gemini(self, transcript: str) -> Dict[str, Any]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("Gemini_api_key")
        if not api_key:
            return self._build_fallback_summary_payload(transcript)

        default_result = {
            "summary": "Chua the tao tom tat tu dong.",
            "decisions": [],
            "action_items": [],
        }

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError("requests not installed for Gemini call") from exc

        transcript_for_summary = self._truncate_for_summary(transcript)

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": get_gemini_summary_prompt(transcript_for_summary)
                        }
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.0,
                "maxOutputTokens": 2048,
            },
        }
        last_error: Optional[str] = None

        for gemini_model in self._get_gemini_model_candidates():
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"

            try:
                resp = requests.post(url, json=payload, timeout=60)
            except Exception as exc:
                last_error = f"request_error: {exc}"
                continue

            if resp.status_code != 200:
                last_error = f"{resp.status_code} {resp.text[:200]}"
                print(f"[AIBridgeService] Gemini summary failed on model {gemini_model}: {last_error}")
                continue

            try:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                parsed = self._extract_json_object(text)
                decisions = self._normalize_decisions(parsed.get("decisions"))
                action_items = self._normalize_action_items(parsed.get("action_items"))
                summary = self._limit_summary_words(parsed.get("summary") or default_result["summary"])
                return {
                    "summary": summary,
                    "decisions": decisions,
                    "action_items": action_items,
                }
            except Exception as exc:
                last_error = f"parse_error: {exc}"
                print(f"[AIBridgeService] Gemini summary parse failed on model {gemini_model}: {exc}")

        print(f"[AIBridgeService] Gemini summary fallback after model attempts: {last_error}")
        return self._build_fallback_summary_payload(transcript_for_summary)

    def _fix_transcript_with_gemini(self, transcript: str) -> str:
        """Use Gemini to rewrite transcript into natural Vietnamese while preserving meaning."""
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

        chunks = self._split_text_for_fix(transcript, self.MAX_TRANSCRIPT_FIX_CHARS_PER_CALL)
        if not chunks:
            return transcript

        fixed_chunks: List[str] = []
        gemini_models = self._get_gemini_model_candidates()

        for index, chunk in enumerate(chunks):
            # Prevent too many API calls for extremely long meetings.
            if index >= self.MAX_FIX_CHUNKS:
                fixed_chunks.extend(chunks[index:])
                break

            prev_context = chunks[index - 1][-500:] if index > 0 else ""
            next_context = chunks[index + 1][:500] if (index + 1) < len(chunks) else ""

            prompt = get_gemini_transcript_fix_prompt(
                chunk=chunk,
                prev_context=prev_context,
                next_context=next_context,
            )

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "responseMimeType": "text/plain",
                    "temperature": 0.0,
                    "maxOutputTokens": 2048,
                }
            }

            chunk_fixed = False
            for gemini_model in gemini_models:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{gemini_model}:generateContent?key={api_key}"
                try:
                    resp = requests.post(url, json=payload, timeout=60)
                except Exception:
                    continue

                if resp.status_code != 200:
                    continue

                try:
                    data = resp.json()
                    fixed_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                except Exception:
                    continue

                if fixed_text:
                    fixed_chunks.append(fixed_text)
                    chunk_fixed = True
                    break

            if not chunk_fixed:
                fixed_chunks.append(chunk)

        merged = "\n".join(part for part in fixed_chunks if part)
        return merged.strip() if merged.strip() else transcript

    def process_audio_groq_gemini(self, input_audio_path: str, chunk_seconds: Optional[int] = None) -> Dict[str, Any]:
        """
        Automated pipeline (optimized for speed):
        1) Split audio into chunks (default 120 seconds for faster processing)
        2) Send all chunks to Groq Whisper in PARALLEL
        3) Optional LLM diarization with Gemini (speaker turns)
        4) Standardize transcript with Gemini (optional via env)
        5) Summarize with Gemini to get summary/decisions/action items
        """

        # Increased chunk size from 90s to 120s = fewer API calls, faster processing
        effective_chunk = self._get_chunk_seconds(chunk_seconds)
        if effective_chunk < 120:
            effective_chunk = 120  # Override for faster processing

        chunks: List[Dict[str, Any]] = []
        combined_transcript: List[str] = []
        speaker_turns: List[Dict[str, Any]] = []

        transcript_for_display = ""
        transcript_for_summary = ""

        # Generate unique session ID for this transcription to prevent Groq caching
        session_id = str(uuid.uuid4())
        print(f"[AIBridgeService] Starting Groq transcription session: {session_id}")

        try:
            # Step 1: Chunk audio
            chunks = self._chunk_audio(input_audio_path, effective_chunk)
            print(f"[AIBridgeService] Created {len(chunks)} chunks, processing in parallel...")

            # Step 2: Process chunks IN PARALLEL for maximum speed
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def transcribe_chunk(args):
                idx, chunk = args
                path = str(chunk.get("path") or "")
                if not path:
                    return idx, ""
                request_id = f"{session_id}_chunk_{idx}"
                try:
                    text = self._transcribe_with_groq(path, request_id=request_id)
                    return idx, text.strip() if text else ""
                except Exception as e:
                    print(f"[AIBridgeService] Chunk {idx} failed: {e}")
                    return idx, ""

            # Use ThreadPoolExecutor for parallel transcription (4 concurrent requests)
            with ThreadPoolExecutor(max_workers=4) as executor:
                tasks = [(idx, chunk) for idx, chunk in enumerate(chunks)]
                results = list(executor.map(transcribe_chunk, tasks))

            # Sort results by index to maintain correct order
            results.sort(key=lambda x: x[0])

            for idx, text in results:
                if text:
                    chunks[idx]["text"] = text
                    combined_transcript.append(text)

            print(f"[AIBridgeService] Parallel transcription completed, {len(combined_transcript)} chunks processed")

            transcript_for_display = "\n".join(combined_transcript).strip()
            transcript_for_summary = transcript_for_display

            if transcript_for_summary:
                # Step 3: Gemini diarization (optional - only if enabled)
                if self._is_llm_diarization_enabled():
                    print(f"[AIBridgeService] Running Gemini diarization...")
                    speaker_turns = self._diarize_with_gemini(chunks)
                    if speaker_turns:
                        diarized_payload = self._build_speaker_transcript(speaker_turns)
                        transcript_for_display = diarized_payload.get("transcript") or transcript_for_display
                        transcript_for_summary = diarized_payload.get("summary_source") or transcript_for_summary
                        print(f"[AIBridgeService] Diarization completed with {len(speaker_turns)} speaker turns")

                # Step 4: Gemini transcript standardization (Groq output -> Gemini polish)
                if self._is_gemini_transcript_fix_enabled():
                    print(f"[AIBridgeService] Running Gemini transcript standardization...")
                    transcript_for_summary = self._fix_transcript_with_gemini(transcript_for_summary)
                    if speaker_turns:
                        # Also polish display transcript so user-facing text is fluent Vietnamese.
                        transcript_for_display = self._fix_transcript_with_gemini(transcript_for_display)

                if not speaker_turns:
                    transcript_for_display = transcript_for_summary

                # Step 5: Gemini summary
                print(f"[AIBridgeService] Running Gemini summary...")
                summary_payload = self._summarize_with_gemini(transcript_for_summary)
                print(f"[AIBridgeService] Summary completed")
            else:
                summary_payload = {
                    "summary": "",
                    "decisions": [],
                    "action_items": [],
                }

            return {
                "transcript": transcript_for_display,
                "summary": summary_payload.get("summary") or "",
                "decisions": summary_payload.get("decisions") or [],
                "action_items": summary_payload.get("action_items") or [],
                "speaker_turns": speaker_turns,
            }
        finally:
            for chunk in chunks:
                path = str(chunk.get("path") or "")
                if not path:
                    continue
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