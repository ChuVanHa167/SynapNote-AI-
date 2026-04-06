import os
import re
import requests
from urllib.parse import urlparse
from typing import Optional, Callable
import time

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
