"""현장별 공정(trade) 목록 조회 검증."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.worker import WorkerCreateRequest
from app.services import site_service, worker_service


async def test_get_trades_returns_distinct_trades_for_site(db_session: AsyncSession, site_id, other_site_id):
    await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="김철수", birth_date="1985-03-15", trade="철거", current_site_id=site_id)
    )
    await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="이영희", birth_date="1990-05-20", trade="목수", current_site_id=site_id)
    )
    await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="박민수", birth_date="1988-01-01", trade="철거", current_site_id=site_id)
    )
    await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="정수현", birth_date="1992-07-07", current_site_id=site_id)
    )
    await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="다른현장", birth_date="1980-01-01", trade="설비", current_site_id=other_site_id)
    )

    result = await site_service.get_trades(db_session, site_id)

    assert sorted(result.data) == ["목수", "철거"]


async def test_get_trades_returns_empty_when_no_workers_assigned(db_session: AsyncSession, site_id):
    result = await site_service.get_trades(db_session, site_id)

    assert result.data == []
