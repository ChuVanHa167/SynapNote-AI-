"""STT (Speech-to-Text) module using Groq Whisper API."""
import os
import tempfile
import shutil
from typing import Optional, Any, Dict


def ensure_ffmpeg_on_path() -> bool:
    """Ensure ffmpeg and ffprobe are available on PATH."""
    if shutil.which("ffmpeg") and shutil.which("ffprobe"):
        return True

    candidates = []

    env_bin = os.getenv("FFMPEG_BIN_DIR")
    if env_bin:
        candidates.append(env_bin)

    localappdata = os.getenv("LOCALAPPDATA", "")
    if localappdata:
        import glob
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


def convert_audio(input_path: str) -> str:
    """Convert audio to WAV format for transcription."""
    if not ensure_ffmpeg_on_path():
        raise RuntimeError("ffmpeg/ffprobe not found")

    import ffmpeg

    temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    temp_wav.close()

    try:
        (
            ffmpeg
            .input(input_path)
            .output(temp_wav.name, acodec="pcm_s16le", ar=16000, ac=1)
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        raise RuntimeError(f"ffmpeg conversion failed: {e}")

    return temp_wav.name


def transcribe(
    wav_path: str,
    profile_config: Optional[Dict[str, Any]] = None
) -> str:
    """Transcribe audio using Groq Whisper API."""
    groq_api_key = os.getenv("GROQ_API_KEY") or os.getenv("Groq_api_key")
    if not groq_api_key:
        raise RuntimeError("Missing GROQ_API_KEY")

    import requests

    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    with open(wav_path, "rb") as f:
        files = {"file": (os.path.basename(wav_path), f, "audio/wav")}
        data = {"model": "whisper-large-v3", "response_format": "text"}
        headers = {"Authorization": f"Bearer {groq_api_key}"}
        resp = requests.post(url, headers=headers, files=files, data=data, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"Groq STT failed: {resp.status_code} {resp.text}")

    return resp.text.strip()


def clean_text(text: str) -> str:
    """Clean and normalize transcribed text."""
    if not text:
        return ""

    # Remove extra whitespace
    text = " ".join(text.split())

    # Fix common transcription issues
    text = text.replace("  ", " ")

    return text.strip()
