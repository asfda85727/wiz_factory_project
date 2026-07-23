"""MinIO(S3 호환) 파일 저장소 클라이언트."""

import io

from minio import Minio

from app.config import settings

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

_client = Minio(
    settings.minio_endpoint,
    access_key=settings.minio_access_key,
    secret_key=settings.minio_secret_key,
    secure=settings.minio_secure,
)


def ensure_bucket() -> None:
    if not _client.bucket_exists(settings.minio_bucket):
        _client.make_bucket(settings.minio_bucket)


def upload_file(object_key: str, data: bytes, content_type: str) -> None:
    _client.put_object(
        settings.minio_bucket, object_key, io.BytesIO(data), length=len(data), content_type=content_type
    )


def download_file(object_key: str) -> bytes:
    response = _client.get_object(settings.minio_bucket, object_key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
