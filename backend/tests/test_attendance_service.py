"""일일 출역 입력: 일괄저장/전일복사/개별수정(audit)/조회 검증."""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AttendanceSiteConflictError, NotFoundError
from app.repositories import attendance_repository
from app.schemas.attendance import AttendanceDailySaveRequest, AttendanceEntryInput, AttendanceUpdateRequest
from app.schemas.worker import WorkerCreateRequest
from app.services import attendance_service, worker_service

WORK_DATE = date(2026, 7, 20)
PREVIOUS_DATE = date(2026, 7, 19)


async def _create_worker(db_session: AsyncSession, name: str = "김철수", trade: str | None = None):
    return await worker_service.create_worker(
        db_session, WorkerCreateRequest(name=name, birth_date="1985-03-15", trade=trade)
    )


async def test_save_daily_creates_new_records(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session, trade="철거")

    result = await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=WORK_DATE,
            entries=[AttendanceEntryInput(worker_id=worker.id, is_present=True)],
        ),
    )

    assert len(result.data) == 1
    assert result.data[0].worker_id == worker.id
    assert result.summary.total_count == 1
    assert result.summary.present_count == 1
    assert result.summary.by_trade == {"철거": 1}


async def test_save_daily_includes_worker_name_in_response(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session, "김철수")

    result = await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    assert result.data[0].worker_name == "김철수"

    daily = await attendance_service.get_daily(db_session, site_id, WORK_DATE, None)
    assert daily.data[0].worker_name == "김철수"


async def test_save_daily_summarizes_absent_and_unclassified_trade(db_session: AsyncSession, actor_id, site_id):
    worker_a = await _create_worker(db_session, "김철수")
    worker_b = await _create_worker(db_session, "이영희", trade="목수")

    result = await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=WORK_DATE,
            entries=[
                AttendanceEntryInput(worker_id=worker_a.id, is_present=True),
                AttendanceEntryInput(worker_id=worker_b.id, is_present=False),
            ],
        ),
    )

    assert result.summary.total_count == 2
    assert result.summary.present_count == 1
    assert result.summary.by_trade == {"미분류": 1}


async def test_save_daily_keeps_workers_fixed_trade_across_resaves(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session, trade="철거")
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    result = await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=WORK_DATE,
            entries=[AttendanceEntryInput(worker_id=worker.id, is_present=False)],
        ),
    )

    assert len(result.data) == 1
    assert result.data[0].trade == "철거"
    assert result.data[0].is_present is False


async def test_save_daily_removes_records_not_in_payload(db_session: AsyncSession, actor_id, site_id):
    worker_a = await _create_worker(db_session, "김철수")
    worker_b = await _create_worker(db_session, "이영희")
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=WORK_DATE,
            entries=[
                AttendanceEntryInput(worker_id=worker_a.id),
                AttendanceEntryInput(worker_id=worker_b.id),
            ],
        ),
    )

    result = await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker_a.id)]
        ),
    )

    assert len(result.data) == 1
    assert result.data[0].worker_id == worker_a.id

    reloaded = await attendance_service.get_daily(db_session, site_id, WORK_DATE, None)
    assert len(reloaded.data) == 1
    assert reloaded.data[0].worker_id == worker_a.id


async def test_save_daily_with_empty_entries_clears_the_day(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session)
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    result = await attendance_service.save_daily(
        db_session, actor_id, AttendanceDailySaveRequest(site_id=site_id, work_date=WORK_DATE, entries=[])
    )

    assert result.data == []
    reloaded = await attendance_service.get_daily(db_session, site_id, WORK_DATE, None)
    assert reloaded.data == []


async def test_save_daily_raises_on_cross_site_conflict(
    db_session: AsyncSession, actor_id, site_id, other_site_id
):
    worker = await _create_worker(db_session)
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    with pytest.raises(AttendanceSiteConflictError):
        await attendance_service.save_daily(
            db_session,
            actor_id,
            AttendanceDailySaveRequest(
                site_id=other_site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
            ),
        )


async def test_get_daily_filters_by_trade(db_session: AsyncSession, actor_id, site_id):
    worker_a = await _create_worker(db_session, "김철수", trade="철거")
    worker_b = await _create_worker(db_session, "이영희", trade="목수")
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=WORK_DATE,
            entries=[
                AttendanceEntryInput(worker_id=worker_a.id),
                AttendanceEntryInput(worker_id=worker_b.id),
            ],
        ),
    )

    result = await attendance_service.get_daily(db_session, site_id, WORK_DATE, "철거")

    assert len(result.data) == 1
    assert result.data[0].worker_id == worker_a.id


async def test_copy_previous_copies_entries_from_previous_day(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session, trade="철거")
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=PREVIOUS_DATE,
            entries=[AttendanceEntryInput(worker_id=worker.id, is_present=True)],
        ),
    )

    result = await attendance_service.copy_previous(db_session, actor_id, site_id, WORK_DATE)

    assert len(result.data) == 1
    assert result.data[0].work_date == WORK_DATE
    assert result.data[0].trade == "철거"


async def test_copy_previous_raises_not_found_when_no_previous_day_data(
    db_session: AsyncSession, actor_id, site_id
):
    with pytest.raises(NotFoundError):
        await attendance_service.copy_previous(db_session, actor_id, site_id, WORK_DATE)


async def test_copy_previous_raises_on_conflict_with_different_site(
    db_session: AsyncSession, actor_id, site_id, other_site_id
):
    worker = await _create_worker(db_session)
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=PREVIOUS_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=other_site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    with pytest.raises(AttendanceSiteConflictError):
        await attendance_service.copy_previous(db_session, actor_id, site_id, WORK_DATE)


async def test_update_attendance_records_audit_log(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session, trade="철거")
    saved = await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )
    attendance_id = saved.data[0].id

    updated = await attendance_service.update_attendance(
        db_session, actor_id, attendance_id, AttendanceUpdateRequest(is_present=False)
    )

    assert updated.is_present is False
    assert updated.trade == "철거"


async def test_update_attendance_not_found_raises(db_session: AsyncSession, actor_id):
    with pytest.raises(NotFoundError):
        await attendance_service.update_attendance(db_session, actor_id, uuid4(), AttendanceUpdateRequest())


async def test_get_worker_monthly_spans_sites(
    db_session: AsyncSession, actor_id, site_id, other_site_id
):
    worker = await _create_worker(db_session, "김철수", trade="철거")
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=date(2026, 7, 5), entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=other_site_id, work_date=date(2026, 7, 6), entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    result = await attendance_service.get_worker_monthly(db_session, worker.id, 2026, 7)

    assert result.worker_name == "김철수"
    assert result.present_days == 2
    assert len(result.data) == 2
    assert {d.site_name for d in result.data} == {"테스트 현장", "다른 현장"}
    assert result.data[0].work_date == date(2026, 7, 5)
    assert result.data[1].work_date == date(2026, 7, 6)


async def test_get_worker_monthly_not_found_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await attendance_service.get_worker_monthly(db_session, uuid4(), 2026, 7)


async def test_get_monthly_returns_records_for_site_and_month(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session)
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=WORK_DATE, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    result = await attendance_service.get_monthly(db_session, site_id, WORK_DATE.year, WORK_DATE.month)

    assert len(result.data) == 1
    assert result.data[0].work_date == WORK_DATE
