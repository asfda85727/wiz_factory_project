"""근로자 신분증/통장 사본 업로드·다운로드 오케스트레이션."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import FileTooLargeError, NotFoundError, UnsupportedFileTypeError
from app.repositories import worker_repository
from app.schemas.worker import WorkerFileType, WorkerFileUploadResult
from app.services.file_storage import ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE_BYTES, download_file, upload_file

_FILE_KEY_ATTR = {
    WorkerFileType.ID_SCAN: "id_scan_file_key",
    WorkerFileType.BANKBOOK_SCAN: "bankbook_scan_file_key",
}


async def upload_worker_file(
    db: AsyncSession, worker_id: UUID, file_type: WorkerFileType, content_type: str, data: bytes
) -> WorkerFileUploadResult:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UnsupportedFileTypeError(f"허용되지 않는 파일 형식입니다: {content_type}")
    if len(data) > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(f"파일 용량이 {MAX_FILE_SIZE_BYTES}바이트를 초과했습니다.")

    object_key = f"workers/{worker_id}/{file_type.value}/{uuid4()}"
    upload_file(object_key, data, content_type)
    setattr(worker, _FILE_KEY_ATTR[file_type], object_key)

    await db.flush()
    return WorkerFileUploadResult(type=file_type, uploaded_at=datetime.now(timezone.utc))


async def download_worker_file(db: AsyncSession, worker_id: UUID, file_type: WorkerFileType) -> bytes:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")

    object_key = getattr(worker, _FILE_KEY_ATTR[file_type])
    if object_key is None:
        raise NotFoundError(f"업로드된 파일이 없습니다: {file_type.value}")

    return download_file(object_key)
