import os
import uuid
from moviepy.editor import VideoFileClip

class AudioProcessingService:
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)

    def extract_audio(self, video_path: str) -> str:
        """
        Trích xuất âm thanh từ file video (.mp4, .mov...) thành file .mp3
        Trả về đường dẫn của file âm thanh, hoặc None nếu có lỗi.
        """
        try:
            filename = os.path.basename(video_path)
            # Create a unique audio filename
            audio_filename = f"audio_{uuid.uuid4().hex[:8]}_{filename.rsplit('.', 1)[0]}.mp3"
            output_audio_path = os.path.join(self.temp_dir, audio_filename)

            # Process with moviepy
            print(f"[AudioService] Đang trích xuất âm thanh từ: {video_path}")
            video = VideoFileClip(video_path)
            audio = video.audio
            
            # Write to file
            audio.write_audiofile(output_audio_path, logger=None) # Hide logs for cleaner output
            
            # Close to free RAM
            audio.close()
            video.close()
            
            print(f"[AudioService] Trích xuất thành công: {output_audio_path}")
            return output_audio_path
            
        except Exception as e:
            print(f"[AudioService] Lỗi khi trích xuất âm thanh: {str(e)}")
            return None
