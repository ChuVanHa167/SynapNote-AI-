import os
import re
import requests
import glob
from urllib.parse import urlparse
from typing import Optional, Callable
import time


def is_youtube_url(url: str) -> bool:
    """Check if URL is a YouTube link (watch/shorts/youtu.be)."""
    url_lower = (url or "").lower()
    return any(
        host in url_lower
        for host in ("youtube.com", "youtu.be", "m.youtube.com")
    )


def _resolve_downloaded_file(local_path: str) -> Optional[str]:
    """Find downloaded file variants from templated output path."""
    if os.path.exists(local_path):
        return local_path

    candidates = glob.glob(f"{local_path}.*")
    if not candidates:
        return None

    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def _download_youtube_with_progress(
    url: str,
    local_path: str,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> bool:
    """Download audio from YouTube using yt-dlp and normalize output path."""
    try:
        from yt_dlp import YoutubeDL  # type: ignore
    except Exception as exc:
        raise RuntimeError(
            "Thiếu thư viện yt-dlp để tải link YouTube. Hãy cài: pip install yt-dlp"
        ) from exc

    if progress_callback:
        progress_callback(0, 0, "Đang kết nối YouTube...")

    def hook(progress_data: dict):
        if not progress_callback:
            return

        status = progress_data.get("status")
        if status == "downloading":
            downloaded = int(progress_data.get("downloaded_bytes") or 0)
            total = int(
                progress_data.get("total_bytes")
                or progress_data.get("total_bytes_estimate")
                or 0
            )
            progress_callback(downloaded, total, "Đang tải audio từ YouTube...")
        elif status == "finished":
            total = int(progress_data.get("total_bytes") or 0)
            progress_callback(total, total, "Đã tải xong, đang xử lý audio...")

    ffmpeg_location = None
    try:
        import imageio_ffmpeg  # type: ignore
        ffmpeg_location = imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        ffmpeg_location = None

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{local_path}.%(ext)s",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "progress_hooks": [hook],
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        },
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "ffmpeg_location": ffmpeg_location,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.extract_info(url, download=True)

    downloaded_path = _resolve_downloaded_file(local_path)
    if not downloaded_path:
        raise RuntimeError("Không tìm thấy file audio sau khi tải từ YouTube")

    if os.path.exists(local_path):
        os.remove(local_path)

    os.replace(downloaded_path, local_path)

    final_size = os.path.getsize(local_path)
    if progress_callback:
        progress_callback(final_size, final_size, "Tải xuống hoàn tất")

    return True

def download_with_progress(
    url: str, 
    local_path: str, 
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    chunk_size: int = 8192
) -> bool:
    """
    Download file from URL with progress tracking
    
    Args:
        url: URL to download from
        local_path: Local path to save file
        progress_callback: Callback(bytes_downloaded, total_bytes, message)
        chunk_size: Size of chunks to download
    
    Returns:
        True if successful
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # YouTube links must be downloaded with yt-dlp, not raw HTTP requests.
        if is_youtube_url(url):
            return _download_youtube_with_progress(url, local_path, progress_callback)

        # Support Google Drive links
        if 'drive.google.com' in url:
            url = convert_google_drive_link(url)
        
        response = requests.get(url, stream=True, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Get total size
        total_size = int(response.headers.get('content-length', 0))
        
        downloaded = 0
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size, "Đang tải xuống...")
        
        if progress_callback:
            progress_callback(downloaded, total_size, "Tải xuống hoàn tất")
        
        return True
        
    except Exception as e:
        if progress_callback:
            progress_callback(0, 0, f"Lỗi tải xuống: {str(e)}")
        raise

def convert_google_drive_link(url: str) -> str:
    """Convert Google Drive sharing link to direct download link"""
    # Match file ID from various Google Drive URL formats
    patterns = [
        r'/d/([a-zA-Z0-9_-]+)',
        r'id=([a-zA-Z0-9_-]+)',
        r'/file/d/([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?export=download&id={file_id}"
    
    return url

def get_filename_from_url(url: str) -> str:
    """Extract filename from URL or Content-Disposition header"""
    if is_youtube_url(url):
        return "youtube_audio.mp3"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Try Content-Disposition header
        cd = response.headers.get('content-disposition', '')
        if cd:
            import re
            fname = re.findall('filename="?([^"]+)"?', cd)
            if fname:
                return fname[0]
        
        # Try URL path
        parsed = urlparse(url)
        path = parsed.path
        if path:
            return os.path.basename(path) or "download"
        
    except Exception:
        pass
    
    return "download"

def is_video_url(url: str) -> bool:
    """Check if URL points to a video file"""
    video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm', '.flv', '.wmv', '.m4v')
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in video_extensions)

def is_audio_url(url: str) -> bool:
    """Check if URL points to an audio file"""
    audio_extensions = ('.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma')
    url_lower = url.lower()
    return any(url_lower.endswith(ext) for ext in audio_extensions)
