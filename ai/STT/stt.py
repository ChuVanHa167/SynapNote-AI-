# audio file -> STT model -> transcript text
# python ai/STT/stt.py

import sys
import os

# add ai folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meeting_summary.summary import prepare_summary_tasks

from pathlib import Path

# --- FFMPEG Handling ---
try:
    import subprocess
    subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except FileNotFoundError:
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        if ffmpeg_dir not in os.environ["PATH"]:
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
        print(f"[STT] Đã cấu hình PATH cho ffmpeg: {ffmpeg_dir}")
    except ImportError:
        print("[STT] CẢNH BÁO: Không tìm thấy ffmpeg. Vui lòng cài đặt ffmpeg hoặc imageio-ffmpeg.")

import whisper
model = whisper.load_model("base")

context = "Cuộc họp công nghệ thông tin, lập trình, AI, Python, backend, database."


# ------------------------------------------------
# chuẩn hóa audio
# ------------------------------------------------
def preprocess_audio(input_path):

    input_path = Path(input_path)
    clean_path = input_path.parent / "clean.wav"

    cmd = [
        "ffmpeg","-y",
        "-i", str(input_path),
        "-ac","1",
        "-ar","16000",
        "-af","loudnorm",
        str(clean_path)
    ]

    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return str(clean_path)


# ------------------------------------------------
# chia audio nếu dài
# ------------------------------------------------
def split_audio(audio_path, chunk_length=30):

    wf = wave.open(audio_path, "rb")
    duration = wf.getnframes() / wf.getframerate()
    wf.close() # Close the wave file after getting duration

    if duration <= chunk_length:
        return [audio_path]

    chunks = []

    for i in range(0, math.ceil(duration/chunk_length)):

        start = i * chunk_length
        output = f"{audio_path}_chunk{i}.wav"

        cmd = [
            "ffmpeg","-y",
            "-i", audio_path,
            "-ss", str(start),
            "-t", str(chunk_length),
            output
        ]

        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        chunks.append(output)

    return chunks


# ------------------------------------------------
# STT
# ------------------------------------------------
def format_timestamp(seconds):
    """Converts seconds to [MM:SS] format"""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"

def speech_to_text(audio_path):
    """
    Transcribes audio to text with timestamps.
    Output format: [00:00 - 00:05]\n[AI]: Text...
    """
    print(f"[STT] Bắt đầu xử lý: {audio_path}")
    
    # Run STT model directly on the audio path
    # Result contains "segments" with start/end times
    result = model.transcribe(
        audio_path,
        task="transcribe",
        language="vi",
        initial_prompt=context,
        fp16=False
    )

    formatted_transcript = []
    
    # Process segments
    for segment in result["segments"]:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"].strip()
        
        # Format: [START - END]\n[AI]: TEXT
        timestamp_range = f"[{format_timestamp(start)} - {format_timestamp(end)}]"
        formatted_line = f"{timestamp_range}\n[AI]: {text}"
        formatted_transcript.append(formatted_line)

    print(f"[STT] Hoàn tất trích xuất {len(formatted_transcript)} đoạn.")
    
    return "\n\n".join(formatted_transcript)


# ------------------------------------------------
# RUN PIPELINE
# ------------------------------------------------
if __name__ == "__main__":

    audio = "ai/audio/test.m4a"

    # STEP 1: STT
    transcript = speech_to_text(audio)

    print("\n===== TRANSCRIPT =====\n")
    print(transcript)


    # STEP 2: SUMMARY TASKS
    tasks = prepare_summary_tasks(transcript)

    print("\n===== SUMMARY TASKS =====\n")

    for i, task in enumerate(tasks):

        print(f"\n---- TASK {i+1} ----\n")
        print(task)