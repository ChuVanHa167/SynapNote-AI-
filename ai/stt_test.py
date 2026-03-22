import os
import re
import ffmpeg
from faster_whisper import WhisperModel
from typing import Dict, Any, Tuple

# =========================
# ⚙️ CONFIG
# =========================
MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "tiny")
LANGUAGE = "vi"
BEAM_SIZE = int(os.getenv("STT_BEAM_SIZE", "1"))
BEST_OF = int(os.getenv("STT_BEST_OF", "1"))
TEMPERATURE = float(os.getenv("STT_TEMPERATURE", "0"))
VAD_FILTER = os.getenv("STT_VAD_FILTER", "true").lower() == "true"
COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")
CPU_THREADS = int(os.getenv("STT_CPU_THREADS", str(os.cpu_count() or 4)))
AUDIO_FILTER = os.getenv("STT_AUDIO_FILTER", "off").lower()

# 📂 PATH
INPUT_AUDIO = "data/input/test.m4a"
OUTPUT_TRANSCRIPT = "data/output/transcript.txt"

_MODEL = None
_MODEL_CACHE: Dict[Tuple[str, str], WhisperModel] = {}


# =========================
# 🎧 AUDIO PREPROCESS
# =========================
def convert_audio(input_path: str) -> str:
    """
    Convert audio về chuẩn:
    - mono
    - 16kHz
    - lọc nhiễu
    """

    output_path = "temp.wav"

    output_kwargs: Dict[str, Any] = {
        "ac": 1,
        "ar": 16000,
    }

    # Optional denoise filter, disabled by default to avoid over-filtering speech.
    if AUDIO_FILTER == "speech_band":
        output_kwargs["af"] = "highpass=f=80, lowpass=f=7000"

    (
        ffmpeg
        .input(input_path)
        .output(output_path, **output_kwargs)
        .overwrite_output()
        .run(quiet=True)
    )

    return output_path


# =========================
# 🧠 STT CORE
# =========================
def get_model(model_size: str = MODEL_SIZE, compute_type: str = COMPUTE_TYPE) -> WhisperModel:
    key = (model_size, compute_type)
    if key not in _MODEL_CACHE:
        print(f"Loading Whisper model: {model_size} ({compute_type})")
        _MODEL_CACHE[key] = WhisperModel(
            model_size,
            device="cpu",
            compute_type=compute_type,
            cpu_threads=max(1, CPU_THREADS),
        )
    return _MODEL_CACHE[key]


def transcribe(audio_path: str, profile_config: Dict[str, Any] | None = None):
    cfg = profile_config or {}
    model_size = str(cfg.get("model_size", MODEL_SIZE))
    compute_type = str(cfg.get("compute_type", COMPUTE_TYPE))
    beam_size = int(cfg.get("beam_size", BEAM_SIZE))
    best_of = int(cfg.get("best_of", BEST_OF))
    temperature = float(cfg.get("temperature", TEMPERATURE))
    vad_filter = bool(cfg.get("vad_filter", VAD_FILTER))
    without_timestamps = bool(cfg.get("without_timestamps", False))
    condition_on_previous_text = bool(cfg.get("condition_on_previous_text", True))

    model = get_model(model_size=model_size, compute_type=compute_type)
    print(f"Transcribing: {os.path.basename(audio_path)}")

    segments, _ = model.transcribe(
        audio_path,
        language=LANGUAGE,
        beam_size=beam_size,
        best_of=best_of,
        temperature=temperature,
        vad_filter=vad_filter,
        condition_on_previous_text=condition_on_previous_text,
        without_timestamps=without_timestamps,
    )

    full_text = []
    for seg in segments:
        text = seg.text.strip()
        if text:
            full_text.append(text)

    return " ".join(full_text)


# =========================
# 🧹 CLEAN TEXT
# =========================
def clean_text(text: str):
    """
    Fix tiếng Việt cơ bản
    """

    text = text.lower().strip()

    replacements = {
        "xin viên": "sinh viên",
        "công ợi": "công nghệ",
        "đồng á": "Đông Á",
        "lam ba": "làm bài",
        "hà nội": "Hà Nội"
    }

    for wrong, correct in replacements.items():
        text = re.sub(rf"\b{wrong}\b", correct, text)

    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)

    text = text.capitalize()

    if not text.endswith("."):
        text += "."

    return text


# =========================
# 🧠 PIPELINE
# =========================
def run_stt():
    print("🎧 Convert audio...")

    wav_path = convert_audio(INPUT_AUDIO)

    try:
        raw = transcribe(wav_path)
        clean = clean_text(raw)

        print("\n===== FINAL TRANSCRIPT =====\n")
        print(clean)

        # 🔥 SAVE FILE (QUAN TRỌNG)
        os.makedirs("data/output", exist_ok=True)

        with open(OUTPUT_TRANSCRIPT, "w", encoding="utf-8") as f:
            f.write(clean)

        print(f"\n💾 Saved → {OUTPUT_TRANSCRIPT}")

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)


# =========================
# 🧪 TEST
# =========================
if __name__ == "__main__":
    run_stt()