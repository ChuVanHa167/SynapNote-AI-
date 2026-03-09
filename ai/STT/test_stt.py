from stt import speech_to_text

audio_path = "../audio/test.m4a"

result = speech_to_text(audio_path)

print(result)