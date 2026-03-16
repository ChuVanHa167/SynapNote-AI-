import os
import uuid
import subprocess

class AudioProcessingService:
    def __init__(self, temp_dir: str = "uploads"):
        self.temp_dir = temp_dir
        self.ffmpeg_path = "ffmpeg" # Default to system PATH
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # --- Robust FFMPEG Path Resolution ---
        try:
            # Check if system ffmpeg exists
            subprocess.run([self.ffmpeg_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print("[AudioService] Sử dụng system ffmpeg.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                import imageio_ffmpeg
                self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                print(f"[AudioService] Sử dụng bundled ffmpeg: {self.ffmpeg_path}")
            except ImportError:
                print("[AudioService] CẢNH BÁO: Không tìm thấy ffmpeg. Vui lòng cài đặt ffmpeg hoặc imageio-ffmpeg.")

    def extract_audio(self, video_path: str) -> str:
        """
        Trích xuất âm thanh cực nhanh bằng FFMPEG (Native Speed)
        """
        try:
            filename = os.path.basename(video_path)
            audio_filename = f"extracted_{uuid.uuid4().hex[:8]}_{filename.rsplit('.', 1)[0]}.mp3"
            output_audio_path = os.path.join(self.temp_dir, audio_filename)

            print(f"[AudioService] Đang trích xuất (FFMPEG): {video_path} -> {output_audio_path}")
            
            # Optimized FFMPEG command for speed
            # -vn: skip video
            # -acodec libmp3lame: use mp3 codec
            # -q:a 4: Variable bitrate quality (4 is roughly 165kbps - fast & good)
            # -y: overwrite
            # -loglevel error: reduce output noise
            cmd = [
                self.ffmpeg_path,
                "-i", video_path,
                "-vn",
                "-acodec", "libmp3lame",
                "-q:a", "4",
                "-y",
                "-loglevel", "error",
                output_audio_path
            ]
            
            subprocess.run(cmd, check=True)
            
            if os.path.exists(output_audio_path):
                print(f"[AudioService] Trích xuất thành công (Native): {output_audio_path}")
                return output_audio_path
            return None
            
        except subprocess.CalledProcessError as e:
            print(f"[AudioService] Lỗi FFMPEG: {str(e)}")
            return None
        except Exception as e:
            print(f"[AudioService] Lỗi hệ thống khi trích xuất: {str(e)}")
            return None
