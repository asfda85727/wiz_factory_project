"""현장 공정(trade) 목록 조회 + 수정/삭제 검증."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, SiteInUseError
from app.schemas.site import SiteUpdateRequest
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


async def test_update_site_changes_fields(db_session: AsyncSession, site_id):
    result = await site_service.update_site(
        db_session, site_id, SiteUpdateRequest(name="변경된 현장명", client_name="변경된 발주처")
    )

    assert result.name == "변경된 현장명"
    assert result.client_name == "변경된 발주처"


async def test_update_site_not_found_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await site_service.update_site(db_session, "00000000-0000-0000-0000-000000000000", SiteUpdateRequest(name="x"))


async def test_delete_site_removes_site(db_session: AsyncSession, site_id):
    await site_service.delete_site(db_session, site_id)

    result = await site_service.list_sites(db_session, None, 20)
    assert all(site.id != site_id for site in result.data)


async def test_delete_site_not_found_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await site_service.delete_site(db_session, "00000000-0000-0000-0000-000000000000")


async def test_delete_site_raises_when_worker_assigned(db_session: AsyncSession, site_id):
    await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="김철수", birth_date="1985-03-15", current_site_id=site_id)
    )

    with pytest.raises(SiteInUseError):
        await site_service.delete_site(db_session, site_id)
