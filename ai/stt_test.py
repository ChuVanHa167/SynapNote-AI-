import os
import re
import ffmpeg
from faster_whisper import WhisperModel

# =========================
# ⚙️ CONFIG
# =========================
MODEL_SIZE = "small"
LANGUAGE = "vi"
CHUNK_DURATION = 30

# 📂 PATH
INPUT_AUDIO = "data/input/test.m4a"
OUTPUT_TRANSCRIPT = "data/output/transcript.txt"


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

    (
        ffmpeg
        .input(input_path)
        .output(
            output_path,
            ac=1,
            ar=16000,
            af="highpass=f=200, lowpass=f=3000"
        )
        .overwrite_output()
        .run(quiet=True)
    )

    return output_path


# =========================
# ✂️ CHIA AUDIO
# =========================
def split_audio(input_path: str):
    probe = ffmpeg.probe(input_path)
    duration = float(probe['format']['duration'])

    chunks = []
    start = 0
    index = 0

    while start < duration:
        output = f"chunk_{index}.wav"

        (
            ffmpeg
            .input(input_path, ss=start, t=CHUNK_DURATION)
            .output(output, acodec='copy')
            .overwrite_output()
            .run(quiet=True)
        )

        chunks.append(output)
        start += CHUNK_DURATION
        index += 1

    return chunks


# =========================
# 🧠 STT CORE
# =========================
def transcribe(audio_path: str):
    print("🔄 Loading model...")

    model = WhisperModel(
        MODEL_SIZE,
        device="cpu",
        compute_type="int8"
    )

    chunks = split_audio(audio_path)
    full_text = []

    for chunk in chunks:
        print(f"🎙️ {chunk}")

        segments, _ = model.transcribe(
            chunk,
            language=LANGUAGE,
            beam_size=8,
            best_of=8,
            temperature=0,
            vad_filter=True
        )

        for seg in segments:
            text = seg.text.strip()
            if text:
                full_text.append(text)

        os.remove(chunk)

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