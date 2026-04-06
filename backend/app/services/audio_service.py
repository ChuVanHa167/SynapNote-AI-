import os
import uuid
import subprocess
import re

try:
    import imageio_ffmpeg
    IMAGEIO_AVAILABLE = True
except ImportError:
    IMAGEIO_AVAILABLE = False

class AudioProcessingService:
    def __init__(self, temp_dir: str = "uploads"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # --- Robust FFMPEG Path Resolution ---
        self.ffmpeg_path = self._detect_ffmpeg_path()
        self.ffprobe_path = self._detect_ffprobe_path()
        
    def _detect_ffmpeg_path(self) -> str:
        """Tự động phát hiện và trả về đường dẫn ffmpeg tốt nhất"""
        # Thứ tự ưu tiên: 1) System PATH, 2) imageio_ffmpeg, 3) Common Windows paths
        
        # 1. Kiểm tra system ffmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=5)
            print("[AudioService] Using system ffmpeg from PATH")
            return "ffmpeg"
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        # 2. Kiểm tra imageio_ffmpeg (bundled)
        if IMAGEIO_AVAILABLE:
            try:
                bundled_path = imageio_ffmpeg.get_ffmpeg_exe()
                if bundled_path and os.path.exists(bundled_path):
                    print(f"[AudioService] Using bundled ffmpeg: {bundled_path}")
                    return bundled_path
            except Exception as e:
                print(f"[AudioService] Failed to get bundled ffmpeg: {e}")
        
        # 3. Common Windows paths for XAMPP/ffmpeg installations
        common_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            r"C:\xampp\ffmpeg\ffmpeg.exe",
        ]
        for path in common_paths:
            if os.path.exists(path):
                print(f"[AudioService] Using ffmpeg from common path: {path}")
                return path
        
        print("[AudioService] WARNING: ffmpeg not found. Please install ffmpeg or run: pip install imageio-ffmpeg")
        return "ffmpeg"  # Fallback, sẽ lỗi khi dùng nhưng để code không crash
    
    def _detect_ffprobe_path(self) -> str:
        """Tự động phát hiện và trả về đường dẫn ffprobe tốt nhất"""
        # ffprobe thường nằm cùng thư mục với ffmpeg
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path) if os.path.isfile(self.ffmpeg_path) else None
        
        candidates = []
        if ffmpeg_dir:
            candidates.append(os.path.join(ffmpeg_dir, "ffprobe.exe"))
            candidates.append(os.path.join(ffmpeg_dir, "ffprobe"))
        
        candidates.extend([
            "ffprobe",
            r"C:\ffmpeg\bin\ffprobe.exe",
            r"C:\Program Files\ffmpeg\bin\ffprobe.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffprobe.exe",
        ])
        
        if IMAGEIO_AVAILABLE:
            try:
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
                if ffmpeg_path:
                    ffprobe_candidate = ffmpeg_path.replace("ffmpeg", "ffprobe")
                    if os.path.exists(ffprobe_candidate):
                        candidates.insert(0, ffprobe_candidate)
            except:
                pass
        
        for path in candidates:
            try:
                if os.path.isfile(path) or path == "ffprobe":
                    subprocess.run([path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=3)
                    return path
            except:
                continue
        
        return "ffprobe"  # Fallback

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
        Lấy thời lượng của file audio/video.
        Thử moviepy trước (không cần ffmpeg binary), sau đó ffmpeg, cuối cùng ffprobe.
        Returns: Duration string dạng "Xm Ys" (ví dụ: "5m 30s")
        """
        # Method 1: Dùng moviepy (pure Python, không cần ffmpeg binary)
        duration = self._get_duration_with_moviepy(file_path)
        if duration and duration != "0m 0s":
            return duration
        
        # Method 2: Dùng ffmpeg làm fallback
        duration = self._get_duration_with_ffmpeg(file_path)
        if duration and duration != "0m 0s":
            return duration
        
        # Method 3: Dùng ffprobe nếu có (chính xác nhất nhưng không có trong bundle)
        if self._ffprobe_exists():
            duration = self._get_duration_with_ffprobe(file_path)
            if duration and duration != "0m 0s":
                return duration
        
        return "0m 0s"
    
    def _ffprobe_exists(self) -> bool:
        """Kiểm tra ffprobe có tồn tại và chạy được không"""
        try:
            if self.ffprobe_path == "ffprobe":
                subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                return True
            elif os.path.exists(self.ffprobe_path):
                subprocess.run([self.ffprobe_path, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
                return True
        except:
            pass
        return False
    
    def _get_duration_with_ffprobe(self, file_path: str) -> str:
        """Lấy thời lượng bằng ffprobe"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout.strip():
                duration_sec = float(result.stdout.strip())
                minutes = int(duration_sec // 60)
                seconds = int(duration_sec % 60)
                return f"{minutes}m {seconds}s"
        except Exception as e:
            print(f"[AudioService] ffprobe duration failed: {e}")
        return None
    
    def _get_duration_with_ffmpeg(self, file_path: str) -> str:
        """Lấy thời lượng bằng ffmpeg (fallback)"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, "-i", file_path],
                capture_output=True,
                text=True,
                timeout=10
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
            print(f"[AudioService] ffmpeg duration failed: {e}")
        return None
    
    def _get_duration_with_moviepy(self, file_path: str) -> str:
        """Lấy thời lượng bằng moviepy (Python library, không cần ffmpeg binary)"""
        try:
            from moviepy.editor import VideoFileClip, AudioFileClip
            
            # Thử VideoFileClip trước
            try:
                with VideoFileClip(file_path) as clip:
                    duration_sec = clip.duration
                    minutes = int(duration_sec // 60)
                    seconds = int(duration_sec % 60)
                    return f"{minutes}m {seconds}s"
            except:
                pass
            
            # Thử AudioFileClip
            try:
                with AudioFileClip(file_path) as clip:
                    duration_sec = clip.duration
                    minutes = int(duration_sec // 60)
                    seconds = int(duration_sec % 60)
                    return f"{minutes}m {seconds}s"
            except:
                pass
                
        except ImportError:
            print("[AudioService] moviepy not available for duration detection")
        except Exception as e:
            print(f"[AudioService] moviepy duration failed: {e}")
        return None

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
