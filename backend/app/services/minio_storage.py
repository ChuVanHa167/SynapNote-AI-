import io
import logging
import mimetypes
import os
from typing import Optional
from urllib.parse import quote, urlparse

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


class MinIOStorage:
    """Service for uploading files to MinIO object storage."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MinIOStorage, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if MinIOStorage._initialized:
            return

        self.endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
        self.access_key = os.getenv("MINIO_ACCESS_KEY")
        self.secret_key = os.getenv("MINIO_SECRET_KEY")
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "synapnote-ai")
        self.secure = os.getenv("MINIO_SECURE", "false").lower() in {"1", "true", "yes"}

        default_scheme = "https" if self.secure else "http"
        default_public = f"{default_scheme}://{self.endpoint}"
        self.public_base_url = os.getenv("MINIO_PUBLIC_BASE_URL", default_public).rstrip("/")

        self.client = None
        if self.access_key and self.secret_key:
            try:
                self.client = Minio(
                    self.endpoint,
                    access_key=self.access_key,
                    secret_key=self.secret_key,
                    secure=self.secure,
                )

                if not self.client.bucket_exists(self.bucket_name):
                    self.client.make_bucket(self.bucket_name)
                    logger.info(f"Created MinIO bucket: {self.bucket_name}")

                logger.info(f"MinIO initialized with bucket: {self.bucket_name}")
            except Exception as exc:
                logger.error(f"Failed to initialize MinIO: {exc}")
                self.client = None
        else:
            logger.warning("MinIO credentials not configured, using local storage only")

        MinIOStorage._initialized = True

    def is_configured(self) -> bool:
        return self.client is not None

    def get_public_url(self, object_name: str) -> str:
        safe_object = quote(object_name)
        return f"{self.public_base_url}/{self.bucket_name}/{safe_object}"

    def _guess_content_type(self, object_name: str) -> str:
        guessed, _ = mimetypes.guess_type(object_name)
        return guessed or "application/octet-stream"

    def upload_file(self, local_path: str, object_name: str, content_type: Optional[str] = None) -> Optional[str]:
        if not self.is_configured():
            logger.warning("MinIO not configured, skipping upload")
            return None

        try:
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=local_path,
                content_type=content_type or self._guess_content_type(object_name),
            )
            url = self.get_public_url(object_name)
            logger.info(f"Uploaded {local_path} to MinIO: {url}")
            return url
        except Exception as exc:
            logger.error(f"Failed to upload {local_path} to MinIO: {exc}")
            return None

    def upload_bytes(self, data: bytes, object_name: str, content_type: Optional[str] = None) -> Optional[str]:
        if not self.is_configured():
            logger.warning("MinIO not configured, skipping upload")
            return None

        try:
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type or self._guess_content_type(object_name),
            )
            url = self.get_public_url(object_name)
            logger.info(f"Uploaded bytes to MinIO: {url}")
            return url
        except Exception as exc:
            logger.error(f"Failed to upload bytes to MinIO: {exc}")
            return None

    def delete_file(self, object_name: str) -> bool:
        if not self.is_configured():
            logger.warning("MinIO not configured, skipping delete")
            return False

        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"Deleted {object_name} from MinIO")
            return True
        except Exception as exc:
            logger.error(f"Failed to delete {object_name} from MinIO: {exc}")
            return False

    def download_file_bytes(self, object_name: str) -> Optional[bytes]:
        if not self.is_configured():
            logger.warning("MinIO not configured, skipping download")
            return None

        response = None
        try:
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            logger.info(f"Downloaded {object_name} from MinIO ({len(data)} bytes)")
            return data
        except S3Error as exc:
            logger.error(f"Failed to download {object_name} from MinIO: {exc}")
            return None
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def extract_object_name_from_url(self, url: str) -> Optional[str]:
        if not url:
            return None

        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return None

        path = parsed.path.lstrip("/")
        prefix = f"{self.bucket_name}/"
        if path.startswith(prefix):
            return path[len(prefix):]
        return None


minio_storage = None


def get_minio_storage():
    global minio_storage
    minio_storage = MinIOStorage()
    return minio_storage
