# audio file -> STT model -> transcrip text
# pip install torch openai-whisper
# python ai/STT/stt.py

import sys
import os

# add ai folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from meeting_summary.summary import prepare_summary_tasks

import whisper
import subprocess
import math
import wave
from pathlib import Path
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
def speech_to_text(audio_path):

    clean_audio = preprocess_audio(audio_path)

    chunks = split_audio(clean_audio)

    transcript = []

    for chunk in chunks:

        result = model.transcribe(
            chunk,
            task="transcribe",
            beam_size=5,
            best_of=5,
            temperature=0,
            initial_prompt=context,
            fp16=False
        )

        transcript.append(result["text"].strip())

        if chunk != clean_audio:
            os.remove(chunk)

    os.remove(clean_audio)

    return " ".join(transcript)


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