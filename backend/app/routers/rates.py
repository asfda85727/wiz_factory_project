"""근로자 단가 등록/이력/수정 라우터. actor(관리자) 식별이 필요해 admin 의존성을 직접 주입받는다."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminContext, get_current_admin
from app.db.session import get_db_session
from app.schemas.rate import (
    WorkerRateCreateRequest,
    WorkerRateListResponse,
    WorkerRateResponse,
    WorkerRateUpdateRequest,
)
from app.services import rate_service

router = APIRouter(tags=["WorkerRates"])


@router.get("/workers/{worker_id}/rates", response_model=WorkerRateListResponse)
async def list_worker_rates(
    worker_id: UUID,
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db_session),
    _admin: AdminContext = Depends(get_current_admin),
) -> WorkerRateListResponse:
    return await rate_service.list_rates(db, worker_id, cursor, limit)


@router.post("/workers/{worker_id}/rates", response_model=WorkerRateResponse, status_code=201)
async def create_worker_rate(
    worker_id: UUID,
    payload: WorkerRateCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminContext = Depends(get_current_admin),
) -> WorkerRateResponse:
    response = await rate_service.create_rate(db, worker_id, UUID(admin.user_id), payload)
    await db.commit()
    return response


@router.patch("/rates/{rate_id}", response_model=WorkerRateResponse)
async def update_worker_rate(
    rate_id: UUID,
    payload: WorkerRateUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminContext = Depends(get_current_admin),
) -> WorkerRateResponse:
    response = await rate_service.update_rate(db, rate_id, UUID(admin.user_id), payload)
    await db.commit()
    return response
