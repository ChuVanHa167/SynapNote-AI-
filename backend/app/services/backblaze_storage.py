import os
import logging
from typing import Optional
from b2sdk.v2 import B2Api, InMemoryAccountInfo, UploadSourceBytes

logger = logging.getLogger(__name__)

class BackblazeStorage:
    """Service for uploading files to Backblaze B2 cloud storage"""
    
    _instance = None
    _initialized = False
    _bucket_name_cached = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BackblazeStorage, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Always check for correct bucket
        correct_bucket = "Synapnote-ai"
        current_bucket = os.getenv("BACKBLAZE_BUCKET_NAME", correct_bucket)
        
        # Force reset if bucket mismatch
        if BackblazeStorage._initialized:
            if BackblazeStorage._bucket_name_cached != current_bucket:
                print(f"[Backblaze] Resetting: cached={BackblazeStorage._bucket_name_cached}, current={current_bucket}")
                BackblazeStorage._initialized = False
                self.b2_api = None
                self.bucket = None
            else:
                return
        
        # Always use correct bucket
        if current_bucket != correct_bucket:
            print(f"[Backblaze] Forcing bucket: {correct_bucket}")
            current_bucket = correct_bucket
            
        self.key_id = os.getenv("BACKBLAZE_KEY_ID")
        self.application_key = os.getenv("BACKBLAZE_APPLICATION_KEY")
        self.bucket_name = current_bucket
        BackblazeStorage._bucket_name_cached = current_bucket
        self.b2_api = None
        self.bucket = None
        
        if self.key_id and self.application_key:
            try:
                info = InMemoryAccountInfo()
                self.b2_api = B2Api(info)
                self.b2_api.authorize_account("production", self.key_id, self.application_key)
                self.bucket = self.b2_api.get_bucket_by_name(self.bucket_name)
                logger.info(f"Backblaze B2 initialized with bucket: {self.bucket_name}")
                BackblazeStorage._initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize Backblaze B2: {e}")
                self.b2_api = None
                self.bucket = None
        else:
            logger.warning("Backblaze credentials not configured, using local storage only")
    
    def is_configured(self) -> bool:
        """Check if Backblaze is properly configured"""
        return self.b2_api is not None and self.bucket is not None
    
    def upload_file(self, local_path: str, remote_filename: str, content_type: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to Backblaze B2
        
        Args:
            local_path: Path to local file
            remote_filename: Name for the file in B2
            content_type: MIME type of the file
            
        Returns:
            Public URL of the uploaded file, or None if upload failed
        """
        if not self.is_configured():
            logger.warning("Backblaze not configured, skipping upload")
            return None
            
        try:
            # Determine content type if not provided
            if content_type is None:
                if remote_filename.endswith('.mp3'):
                    content_type = 'audio/mpeg'
                elif remote_filename.endswith('.mp4'):
                    content_type = 'video/mp4'
                elif remote_filename.endswith('.mov'):
                    content_type = 'video/quicktime'
                elif remote_filename.endswith('.wav'):
                    content_type = 'audio/wav'
                else:
                    content_type = 'application/octet-stream'
            
            # Upload file
            file_version = self.bucket.upload_local_file(
                local_file=local_path,
                file_name=remote_filename,
                content_type=content_type
            )
            
            # Get public URL (files in B2 are public by default if bucket is public)
            # Format: https://fXXX.backblazeb2.com/file/bucket-name/file-name
            download_url = self.b2_api.get_download_url_for_file_name(
                bucket_name=self.bucket_name,
                file_name=remote_filename
            )
            
            logger.info(f"Uploaded {local_path} to Backblaze B2: {download_url}")
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload {local_path} to Backblaze B2: {e}")
            return None
    
    def upload_bytes(self, data: bytes, remote_filename: str, content_type: Optional[str] = None) -> Optional[str]:
        """
        Upload bytes directly to Backblaze B2
        
        Args:
            data: File data as bytes
            remote_filename: Name for the file in B2
            content_type: MIME type of the file
            
        Returns:
            Public URL of the uploaded file, or None if upload failed
        """
        if not self.is_configured():
            logger.warning("Backblaze not configured, skipping upload")
            return None
            
        try:
            # Determine content type if not provided
            if content_type is None:
                if remote_filename.endswith('.mp3'):
                    content_type = 'audio/mpeg'
                elif remote_filename.endswith('.mp4'):
                    content_type = 'video/mp4'
                elif remote_filename.endswith('.mov'):
                    content_type = 'video/quicktime'
                elif remote_filename.endswith('.wav'):
                    content_type = 'audio/wav'
                else:
                    content_type = 'application/octet-stream'
            
            # Upload bytes
            file_version = self.bucket.upload_bytes(
                data_bytes=data,
                file_name=remote_filename,
                content_type=content_type
            )
            
            # Get public URL
            download_url = self.b2_api.get_download_url_for_file_name(
                bucket_name=self.bucket_name,
                file_name=remote_filename
            )
            
            logger.info(f"Uploaded bytes to Backblaze B2: {download_url}")
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload bytes to Backblaze B2: {e}")
            return None
    
    def delete_file(self, remote_filename: str) -> bool:
        """
        Delete a file from Backblaze B2
        
        Args:
            remote_filename: Name of the file in B2
            
        Returns:
            True if deletion was successful, False otherwise
        """
        if not self.is_configured():
            logger.warning("Backblaze not configured, skipping delete")
            return False
            
        try:
            file_version = self.bucket.delete_file(remote_filename)
            logger.info(f"Deleted {remote_filename} from Backblaze B2")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {remote_filename} from Backblaze B2: {e}")
            return False
    
    def download_file_bytes(self, remote_filename: str) -> Optional[bytes]:
        """
        Download a file from Backblaze B2 as bytes
        
        Args:
            remote_filename: Name of the file in B2 (e.g., "audio/xxx.mp3")
            
        Returns:
            File content as bytes, or None if download failed
        """
        if not self.is_configured():
            logger.warning("Backblaze not configured, skipping download")
            return None
            
        try:
            # Download file using B2 SDK
            downloaded_file = self.bucket.download_file_by_name(remote_filename)
            file_bytes = downloaded_file.response.iter_content()
            
            # Collect all chunks into bytes
            data = b''.join(chunk for chunk in file_bytes)
            
            logger.info(f"Downloaded {remote_filename} from Backblaze B2 ({len(data)} bytes)")
            return data
            
        except Exception as e:
            logger.error(f"Failed to download {remote_filename} from Backblaze B2: {e}")
            return None

# Singleton instance
backblaze_storage = None

def get_backblaze_storage():
    """Get Backblaze storage instance with forced bucket name."""
    global backblaze_storage
    # Force create new instance to ensure correct bucket
    backblaze_storage = BackblazeStorage()
    return backblaze_storage
