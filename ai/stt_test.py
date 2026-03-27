import os
import re
import ffmpeg
from faster_whisper import WhisperModel
from typing import Dict, Any, Tuple

# =========================
# ⚙️ CONFIG
# =========================
MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "medium") # mạnh nhất large-v3
LANGUAGE = "vi"
BEAM_SIZE = int(os.getenv("STT_BEAM_SIZE", "8"))
BEST_OF = int(os.getenv("STT_BEST_OF", "5"))
TEMPERATURE = float(os.getenv("STT_TEMPERATURE", "0"))
VAD_FILTER = os.getenv("STT_VAD_FILTER", "true").lower() == "true"
COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")
CPU_THREADS = int(os.getenv("STT_CPU_THREADS", str(os.cpu_count() or 4)))
AUDIO_FILTER = os.getenv("STT_AUDIO_FILTER", "speech_band").lower()
REPETITION_PENALTY = 1.1
NO_REPEAT_NGRAM_SIZE = 3

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
        output_kwargs["af"] = "loudnorm,highpass=f=80,lowpass=f=7000"

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
    repetition_penalty = float(cfg.get("repetition_penalty", REPETITION_PENALTY))
    no_repeat_ngram_size = int(cfg.get("no_repeat_ngram_size", NO_REPEAT_NGRAM_SIZE))
    condition_on_previous_text=True

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
        repetition_penalty=repetition_penalty,
        no_repeat_ngram_size=no_repeat_ngram_size,
    )

    full_text = []
    dynamic_context = ""

    for i, seg in enumerate(segments):

        text = seg.text.strip()

        if not text:
            continue

        # 🔥 cập nhật context theo những đoạn trước
        if i < 3:
            dynamic_context += " " + text

        full_text.append(text)

    return " ".join(full_text)



# =========================
# 🧹 CLEAN TEXT
# =========================
def clean_text(text: str):
    """
    Fix tiếng Việt cơ bản
    """

    text = text.strip()

    replacements = {
        # sai âm / Việt hóa
        "xin viên": "sinh viên",
        "xinh viên": "sinh viên",
        "sinh viên": "sinh viên",
        "công ợi": "công nghệ",
        "công nghe": "công nghệ",
        "công ở thông tin": "công nghệ thông tin",
        "hoa công": "khoa công",
        "đồng á": "Đông Á",
        "trở ra học": "trường đại học",
        "lâm ba": "làm bài",
        "làm ba": "làm bài",
        "trử vấn": "chữ văn",
        "trử": "chữ",
        "vấn ha": "Văn Hà",

        # công nghệ / học thuật
        "phần mềm": "phần mềm",
        "triển chai": "triển khai",
        "giái pháp": "giải pháp",
        "xử lý": "xử lý",
        "phân tích": "phân tích",
        "khoa công nghệ thông tin": "khoa công nghệ thông tin",
        "trường đại học đông á": "trường đại học Đông Á",
        "đại học đông á": "Đại học Đông Á",

        # tiếng anh / tech
        "pai thon": "Python",
        "phai thon": "Python",
        "paiton": "Python",
        "bét en": "backend",
        "back en": "backend",
        "phờ rông đền": "frontend",
        "front end": "frontend",
        "đê ta bây": "database",
        "dat abase": "database",
        "a pi": "API",
        "api ai": "API",
        "ai ai": "AI",
        "mi chin lening": "machine learning",
        "mác chin lening": "machine learning",
        "râu đờ map": "roadmap",
        "đét lai n": "deadline",
        "mi ting": "meeting",
        "re viu": "review",
        "đi bát": "debug",
        "đi plôi": "deploy",
        "ser vơ": "server",
        "cli ent": "client",
        "jê vít": "JavaScript",
        "rê ác": "React",
        "vừ": "Vue",
        "tài pô": "TypeScript",
        "no đê": "Node",
        "dô cơ": "Docker",
        "cư ber nê tis": "Kubernetes",
        "tê st": "test",
        "yu nít": "unit",
        "tê st kê xơ": "test case",
        "vi te xơ": "version control",
        "gít": "Git",
        "gít hab": "GitHub",
        "gít lab": "GitLab",
        "brến": "branch",
        "pul ri quét": "pull request",
        "mer": "merge",
        "kô mít": "commit",
        "re bê xơ": "rebase",
        "xơ cóc": "checkout",
        "klôn": "clone",
        "fốc": "fork",
        "tao xơ kê": "task key",
        "is siu": "issue",
        "bác lốc": "backlog",
        "sô rí": "story",
        "e pôn": "Agile Point",
        "sprin": "sprint",
        "scrôm": "Scrum",
        "po": "Product Owner",
        "sm": "Scrum Master",
        "a đôi": "audit",
        "tách cơ": "tech check",

        # từ họp hành
        "nhiệm vụ": "nhiệm vụ",
        "công việc": "công việc",
        "phân công": "phân công",
        "báo cáo": "báo cáo",
        "tiến độ": "tiến độ",
        "mục tiêu": "mục tiêu",
        "kết luận": "kết luận",
        "cuộc hộp": "cuộc họp",
        "chéo dài": "kéo dài",
        "ưu tiên": "ưu tiên",
        "yêu cầu": "yêu cầu",
        "đề xuất": "đề xuất",
        "thống nhất": "thống nhất",
        "thoả thuận": "thoả thuận",
        "hạn chế": "hạn chế",
        "rủi ro": "rủi ro",
        "thách thức": "thách thức",
        "cơ hội": "cơ hội",
        "phân tích": "phân tích",
        "đánh giá": "đánh giá",
        "cải tiến": "cải tiến",
        "nâng cao": "nâng cao",
        "tối ưu": "tối ưu",
        "hiệu suất": "hiệu suất",
        "chất lượng": "chất lượng",
        "độ ưu tiên": "độ ưu tiên",
        "chi phí": "chi phí",
        "ngân sách": "ngân sách",
        "tài nguyên": "tài nguyên",
        "lịch trình": "lịch trình",
        "thời hạn": "thời hạn",
        "hoàn thành": "hoàn thành",
        "giao lưu": "giao lưu",
        "phản hồi": "phản hồi",
        "đóng góp": "đóng góp",
        "tuyên bố": "tuyên bố",
        "công bố": "công bố",
        "thông báo": "thông báo",
        "cập nhật": "cập nhật",
        "thay đổi": "thay đổi",
        "bổ sung": "bổ sung",
        "hủy bỏ": "hủy bỏ",
        "hoãn lại": "hoãn lại",
        "tạm ngừng": "tạm ngừng",
        "tiếp tục": "tiếp tục",
    }

    for wrong, correct in replacements.items():
        text = re.sub(rf"\b{wrong}\b", correct, text)

    text = re.sub(r"\b(à|ờ|ừ|ừm|uh|um|kiểu như|nói chung là|thực ra|thật ra)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b(\w+)( \1\b)+", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text)

    if not text.endswith("."):
        text += "."

    return text

# =========================
# 🧠 HOTWORDS
# =========================

def extract_hotwords(text):

    words = text.split()

    freq = {}

    for w in words:
        w = w.lower()
        if len(w) < 4:
            continue
        freq[w] = freq.get(w, 0) + 1

    # lấy top từ lặp nhiều
    hot = sorted(freq.items(), key=lambda x: x[1], reverse=True)

    hotwords = [w for w, c in hot[:10]]

    return ", ".join(hotwords)

# =========================
# 🧠 PIPELINE
# =========================
def run_stt():
    print("🎧 Convert audio...")

    wav_path = convert_audio(INPUT_AUDIO)

    try:
        raw = transcribe(wav_path)
        clean = clean_text(raw)

        auto_hotwords = extract_hotwords(raw)
        print("🔥 HOTWORDS AUTO:", auto_hotwords)

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