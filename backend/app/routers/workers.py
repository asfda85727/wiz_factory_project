"""근로자 CRUD + 파일 업로드/다운로드 + 현장이동이력 라우터.

OpenAPI 계약: backend/openapi/workers.yaml
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.db.session import get_db_session
from app.schemas.worker import (
    SiteHistoryResponse,
    WorkerCreateRequest,
    WorkerFileType,
    WorkerFileUploadResult,
    WorkerListResponse,
    WorkerResponse,
    WorkerUpdateRequest,
)
from app.services import site_history_service, worker_file_service, worker_service

router = APIRouter(prefix="/workers", tags=["Workers"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=WorkerListResponse)
async def list_workers(
    search: str | None = None,
    status: str | None = None,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> WorkerListResponse:
    return await worker_service.list_workers(db, search, status, cursor, limit)


@router.post("", response_model=WorkerResponse, status_code=201)
async def create_worker(payload: WorkerCreateRequest, db: AsyncSession = Depends(get_db_session)) -> WorkerResponse:
    response = await worker_service.create_worker(db, payload)
    await db.commit()
    return response


@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(worker_id: UUID, db: AsyncSession = Depends(get_db_session)) -> WorkerResponse:
    return await worker_service.get_worker(db, worker_id)


@router.patch("/{worker_id}", response_model=WorkerResponse)
async def update_worker(
    worker_id: UUID, payload: WorkerUpdateRequest, db: AsyncSession = Depends(get_db_session)
) -> WorkerResponse:
    response = await worker_service.update_worker(db, worker_id, payload)
    await db.commit()
    return response


@router.post("/{worker_id}/files", response_model=WorkerFileUploadResult, status_code=201)
async def upload_worker_file(
    worker_id: UUID,
    type: WorkerFileType = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
) -> WorkerFileUploadResult:
    data = await file.read()
    result = await worker_file_service.upload_worker_file(
        db, worker_id, type, file.content_type or "application/octet-stream", data
    )
    await db.commit()
    return result


@router.get("/{worker_id}/files/{type}")
async def download_worker_file(
    worker_id: UUID, type: WorkerFileType, db: AsyncSession = Depends(get_db_session)
) -> Response:
    data = await worker_file_service.download_worker_file(db, worker_id, type)
    return Response(content=data, media_type="application/octet-stream")


@router.get("/{worker_id}/site-history", response_model=SiteHistoryResponse)
async def get_worker_site_history(
    worker_id: UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> SiteHistoryResponse:
    return await site_history_service.get_site_history(db, worker_id, cursor, limit)
