# audio file -> STT model -> transcrip text
# pip install torch openai-whisper

import whisper

model = whisper.load_model("base")

def speech_to_text(audio_path):

    result = model.transcribe(audio_path, language = "vi", task="transcribe", beam_size = 5, best_of = 5, initial_prompt="Cuộc họp sinh viên khoa công nghệ thông tin")

    transcript = result["text"]

    return transcript