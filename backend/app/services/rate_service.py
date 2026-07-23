"""단가 등록/수정 — 기간 겹침 검사 + audit 기록(기획서 10번: worker_rates, rate_audit_log)."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, RatePeriodOverlapError
from app.models.rate_audit_log import RateAuditLog
from app.models.worker_rate import WorkerRate
from app.repositories import rate_repository, worker_repository
from app.schemas.common import CursorPage
from app.schemas.rate import (
    WorkerRateCreateRequest,
    WorkerRateListResponse,
    WorkerRateResponse,
    WorkerRateUpdateRequest,
)


def _rate_summary(rate: WorkerRate) -> str:
    return f"daily_rate={rate.daily_rate}, effective_from={rate.effective_from}, effective_to={rate.effective_to}"


def _overlap_detail(overlapping: WorkerRate) -> str:
    return f"기존 단가 기간과 겹칩니다: {overlapping.effective_from}~{overlapping.effective_to or '현재'}"


async def create_rate(
    db: AsyncSession, worker_id: UUID, actor_id: UUID, payload: WorkerRateCreateRequest
) -> WorkerRateResponse:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")

    overlapping = await rate_repository.find_overlapping_rate(
        db, worker_id, payload.effective_from, payload.effective_to
    )
    if overlapping is not None:
        raise RatePeriodOverlapError(_overlap_detail(overlapping))

    rate = WorkerRate(
        worker_id=worker_id,
        daily_rate=payload.daily_rate,
        effective_from=payload.effective_from,
        effective_to=payload.effective_to,
        created_by=actor_id,
    )
    db.add(rate)
    await db.flush()

    db.add(RateAuditLog(rate_id=rate.id, changed_by=actor_id, old_value=None, new_value=_rate_summary(rate)))
    await db.flush()
    await db.refresh(rate)
    return WorkerRateResponse.model_validate(rate)


async def update_rate(
    db: AsyncSession, rate_id: UUID, actor_id: UUID, payload: WorkerRateUpdateRequest
) -> WorkerRateResponse:
    rate = await rate_repository.get_rate_by_id(db, rate_id)
    if rate is None:
        raise NotFoundError(f"단가를 찾을 수 없습니다: {rate_id}")

    old_value = _rate_summary(rate)

    if payload.effective_to is not None:
        overlapping = await rate_repository.find_overlapping_rate(
            db, rate.worker_id, rate.effective_from, payload.effective_to, exclude_rate_id=rate.id
        )
        if overlapping is not None:
            raise RatePeriodOverlapError(_overlap_detail(overlapping))
        rate.effective_to = payload.effective_to

    if payload.daily_rate is not None:
        rate.daily_rate = payload.daily_rate

    db.add(
        RateAuditLog(rate_id=rate.id, changed_by=actor_id, old_value=old_value, new_value=_rate_summary(rate))
    )
    await db.flush()
    await db.refresh(rate)
    return WorkerRateResponse.model_validate(rate)


async def list_rates(
    db: AsyncSession, worker_id: UUID, cursor: str | None, limit: int
) -> WorkerRateListResponse:
    rows, next_cursor, has_more = await rate_repository.list_worker_rates(db, worker_id, cursor, limit)
    return WorkerRateListResponse(
        data=[WorkerRateResponse.model_validate(r) for r in rows],
        pagination=CursorPage(next_cursor=next_cursor, has_more=has_more),
    )
