"""단가 등록/수정 — 기간 겹침 검사 검증."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import RatePeriodOverlapError
from app.schemas.rate import WorkerRateCreateRequest, WorkerRateUpdateRequest
from app.schemas.worker import WorkerCreateRequest
from app.services import rate_service, worker_service


async def _create_worker(db_session: AsyncSession):
    return await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="김철수", birth_date="1985-03-15")
    )


async def test_create_rate_succeeds_for_non_overlapping_period(db_session: AsyncSession, actor_id):
    worker = await _create_worker(db_session)

    rate = await rate_service.create_rate(
        db_session,
        worker.id,
        actor_id,
        WorkerRateCreateRequest(daily_rate=150000, effective_from="2026-01-01", effective_to="2026-06-30"),
    )

    assert rate.daily_rate == 150000


async def test_create_rate_raises_on_overlap(db_session: AsyncSession, actor_id):
    worker = await _create_worker(db_session)
    await rate_service.create_rate(
        db_session,
        worker.id,
        actor_id,
        WorkerRateCreateRequest(daily_rate=150000, effective_from="2026-01-01", effective_to="2026-06-30"),
    )

    with pytest.raises(RatePeriodOverlapError):
        await rate_service.create_rate(
            db_session,
            worker.id,
            actor_id,
            WorkerRateCreateRequest(daily_rate=160000, effective_from="2026-03-01", effective_to=None),
        )


async def test_create_rate_allows_adjacent_non_overlapping_period(db_session: AsyncSession, actor_id):
    worker = await _create_worker(db_session)
    await rate_service.create_rate(
        db_session,
        worker.id,
        actor_id,
        WorkerRateCreateRequest(daily_rate=150000, effective_from="2026-01-01", effective_to="2026-06-30"),
    )

    second = await rate_service.create_rate(
        db_session,
        worker.id,
        actor_id,
        WorkerRateCreateRequest(daily_rate=160000, effective_from="2026-07-01", effective_to=None),
    )

    assert second.daily_rate == 160000


async def test_update_rate_raises_when_extending_into_overlap(db_session: AsyncSession, actor_id):
    worker = await _create_worker(db_session)
    first = await rate_service.create_rate(
        db_session,
        worker.id,
        actor_id,
        WorkerRateCreateRequest(daily_rate=150000, effective_from="2026-01-01", effective_to="2026-03-31"),
    )
    await rate_service.create_rate(
        db_session,
        worker.id,
        actor_id,
        WorkerRateCreateRequest(daily_rate=160000, effective_from="2026-04-01", effective_to="2026-06-30"),
    )

    with pytest.raises(RatePeriodOverlapError):
        await rate_service.update_rate(
            db_session, first.id, actor_id, WorkerRateUpdateRequest(effective_to="2026-04-15")
        )
