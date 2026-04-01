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
            print("[AudioService] Using system ffmpeg.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            try:
                import imageio_ffmpeg
                self.ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                print(f"[AudioService] Using bundled ffmpeg: {self.ffmpeg_path}")
            except ImportError:
                print("[AudioService] WARNING: ffmpeg not found. Please install ffmpeg or imageio-ffmpeg.")

    def _probe_audio_codec(self, video_path: str) -> str:
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-i", video_path],
                capture_output=True,
                text=True,
                check=False,
            )
            out = result.stderr or result.stdout or ""
            match = None
            for line in out.splitlines():
                if "Audio:" in line:
                    match = line
                    break
            if match:
                parts = match.split("Audio:")[-1].split(",")[0].strip()
                return parts
        except Exception:
            pass
        return ""

    def get_duration(self, file_path: str) -> str:
        """
        Lấy thời lượng của file audio/video sử dụng ffprobe hoặc ffmpeg.
        Returns: Duration string dạng "Xm Ys" (ví dụ: "5m 30s")
        """
        try:
            # Try ffprobe first (more reliable for metadata)
            ffprobe_path = "ffprobe"
            try:
                subprocess.run([ffprobe_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            except (FileNotFoundError, subprocess.CalledProcessError):
                try:
                    import imageio_ffmpeg
                    # Use the same ffmpeg binary for ffprobe functionality
                    ffprobe_path = self.ffmpeg_path
                except ImportError:
                    ffprobe_path = self.ffmpeg_path

            result = subprocess.run(
                [ffprobe_path, "-i", file_path],
                capture_output=True,
                text=True,
                check=False,
            )

            # Parse duration from output
            out = result.stderr or result.stdout or ""

            # Look for "Duration: HH:MM:SS.ms" pattern
            import re
            duration_match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d+)", out)

            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))

                total_minutes = hours * 60 + minutes
                return f"{total_minutes}m {seconds}s"

            # Fallback: try ffmpeg with show_info
            result = subprocess.run(
                [self.ffmpeg_path, "-i", file_path, "-f", "null", "-"],
                capture_output=True,
                text=True,
                check=False,
            )
            out = result.stderr or result.stdout or ""
            duration_match = re.search(r"Duration:\s*(\d{2}):(\d{2}):(\d{2})\.(\d+)", out)

            if duration_match:
                hours = int(duration_match.group(1))
                minutes = int(duration_match.group(2))
                seconds = int(duration_match.group(3))

                total_minutes = hours * 60 + minutes
                return f"{total_minutes}m {seconds}s"

        except Exception as e:
            print(f"[AudioService] Error getting duration: {str(e)}")

        return "0m 0s"

    def extract_audio(self, video_path: str) -> str:
        """
        Trích xuất âm thanh ưu tiên "copy" (siêu nhanh) nếu codec đã là aac/mp3;
        fallback sang mp3 encode khi cần.
        """
        try:
            filename = os.path.basename(video_path)
            base_name = filename.rsplit('.', 1)[0]
            codec = self._probe_audio_codec(video_path).lower()

            can_copy_aac = "aac" in codec
            can_copy_mp3 = "mp3" in codec

            if can_copy_aac:
                audio_filename = f"extracted_{uuid.uuid4().hex[:8]}_{base_name}.m4a"
                output_audio_path = os.path.join(self.temp_dir, audio_filename)
                copy_cmd = [
                    self.ffmpeg_path,
                    "-i", video_path,
                    "-vn",
                    "-acodec", "copy",
                    "-y",
                    "-loglevel", "error",
                    output_audio_path,
                ]
                try:
                    subprocess.run(copy_cmd, check=True)
                    if os.path.exists(output_audio_path):
                        print(f"[AudioService] Copy audio thành công: {output_audio_path}")
                        return output_audio_path
                except subprocess.CalledProcessError:
                    print("[AudioService] Copy AAC thất bại, fallback encode.")

            if can_copy_mp3:
                audio_filename = f"extracted_{uuid.uuid4().hex[:8]}_{base_name}.mp3"
                output_audio_path = os.path.join(self.temp_dir, audio_filename)
                copy_cmd = [
                    self.ffmpeg_path,
                    "-i", video_path,
                    "-vn",
                    "-acodec", "copy",
                    "-y",
                    "-loglevel", "error",
                    output_audio_path,
                ]
                try:
                    subprocess.run(copy_cmd, check=True)
                    if os.path.exists(output_audio_path):
                        print(f"[AudioService] Copy audio thành công: {output_audio_path}")
                        return output_audio_path
                except subprocess.CalledProcessError:
                    print("[AudioService] Copy MP3 thất bại, fallback encode.")

            # Fallback encode to MP3
            audio_filename = f"extracted_{uuid.uuid4().hex[:8]}_{base_name}.mp3"
            output_audio_path = os.path.join(self.temp_dir, audio_filename)
            print(f"[AudioService] Đang mã hóa MP3 (fallback): {video_path} -> {output_audio_path}")
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
                print(f"[AudioService] Trích xuất thành công: {output_audio_path}")
                return output_audio_path
            return None

        except subprocess.CalledProcessError as e:
            print(f"[AudioService] Lỗi FFMPEG: {str(e)}")
            return None
        except Exception as e:
            print(f"[AudioService] Lỗi hệ thống khi trích xuất: {str(e)}")
            return None
