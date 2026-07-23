"""월별 정산 파이프라인: 출역+단가 연결, held 처리, 재계산 멱등성 검증."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.attendance import AttendanceDailySaveRequest, AttendanceEntryInput
from app.schemas.rate import WorkerRateCreateRequest
from app.schemas.worker import WorkerCreateRequest, WorkerStatus, WorkerUpdateRequest
from app.services import attendance_service, payroll_service, rate_service, worker_service

TARGET_YEAR = 2026
TARGET_MONTH = 7
PRESENT_DATES = [date(2026, 7, d) for d in range(1, 11)]  # 10일 출역


async def _create_active_worker(db_session: AsyncSession, name: str = "김철수", trade: str | None = None):
    worker = await worker_service.create_worker(
        db_session, WorkerCreateRequest(name=name, birth_date="1985-03-15", trade=trade)
    )
    return await worker_service.update_worker(
        db_session,
        worker.id,
        WorkerUpdateRequest(
            status=WorkerStatus.ACTIVE,
            phone="010-1234-5678",
            resident_registration_number="850315-1234567",
            bank_account_number="123-456-789",
        ),
    )


async def _record_attendance(db_session: AsyncSession, actor_id, site_id, worker_id, dates):
    for work_date in dates:
        await attendance_service.save_daily(
            db_session,
            actor_id,
            AttendanceDailySaveRequest(
                site_id=site_id, work_date=work_date, entries=[AttendanceEntryInput(worker_id=worker_id)]
            ),
        )


async def test_recalculate_computes_ok_for_active_worker_with_rate(
    db_session: AsyncSession, actor_id, site_id
):
    worker = await _create_active_worker(db_session)
    await rate_service.create_rate(
        db_session, worker.id, actor_id, WorkerRateCreateRequest(daily_rate=150_000, effective_from="2026-01-01")
    )
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)

    result = await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    row = next(r for r in result.data if r.worker_id == worker.id)
    assert row.calc_status == "ok"
    assert row.work_days == 10
    assert row.gross_pay == 150_000 * 10
    assert row.net_pay == row.gross_pay - row.income_tax - row.local_tax - row.employment_insurance - row.national_pension - row.health_insurance - row.long_term_care


async def test_recalculate_holds_provisional_worker(db_session: AsyncSession, actor_id, site_id):
    worker = await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="이영희", birth_date="1990-05-20")
    )
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)

    result = await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    row = next(r for r in result.data if r.worker_id == worker.id)
    assert row.calc_status == "held"
    assert row.gross_pay == 0
    assert row.work_days == 10


async def test_recalculate_holds_active_worker_without_rate(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_active_worker(db_session, "박민수")
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)

    result = await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    row = next(r for r in result.data if r.worker_id == worker.id)
    assert row.calc_status == "held"
    assert row.gross_pay == 0


async def test_recalculate_counts_only_present_days_in_target_month(
    db_session: AsyncSession, actor_id, site_id
):
    worker = await _create_active_worker(db_session)
    await rate_service.create_rate(
        db_session, worker.id, actor_id, WorkerRateCreateRequest(daily_rate=150_000, effective_from="2026-01-01")
    )
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=date(2026, 7, 1),
            entries=[AttendanceEntryInput(worker_id=worker.id, is_present=True)],
        ),
    )
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=date(2026, 7, 2),
            entries=[AttendanceEntryInput(worker_id=worker.id, is_present=False)],
        ),
    )
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id,
            work_date=date(2026, 6, 30),
            entries=[AttendanceEntryInput(worker_id=worker.id, is_present=True)],
        ),
    )

    result = await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    row = next(r for r in result.data if r.worker_id == worker.id)
    assert row.work_days == 1


async def test_recalculate_is_idempotent_on_rerun(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_active_worker(db_session)
    await rate_service.create_rate(
        db_session, worker.id, actor_id, WorkerRateCreateRequest(daily_rate=150_000, effective_from="2026-01-01")
    )
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)

    await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)
    await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    listed = await payroll_service.get_month(db_session, TARGET_YEAR, TARGET_MONTH)
    matching = [r for r in listed.data if r.worker_id == worker.id]
    assert len(matching) == 1


async def test_recalculate_removes_stale_result_when_attendance_removed(
    db_session: AsyncSession, actor_id, site_id
):
    worker = await _create_active_worker(db_session)
    await rate_service.create_rate(
        db_session, worker.id, actor_id, WorkerRateCreateRequest(daily_rate=150_000, effective_from="2026-01-01")
    )
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)
    await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    # 출역 기록을 전부 제거(빈 명단으로 저장 = reconcile 삭제) 후 재계산
    for work_date in PRESENT_DATES:
        await attendance_service.save_daily(
            db_session, actor_id, AttendanceDailySaveRequest(site_id=site_id, work_date=work_date, entries=[])
        )
    await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    listed = await payroll_service.get_month(db_session, TARGET_YEAR, TARGET_MONTH)
    assert all(r.worker_id != worker.id for r in listed.data)


async def test_recalculate_includes_worker_trade(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_active_worker(db_session, "김철수", trade="철거")
    await rate_service.create_rate(
        db_session, worker.id, actor_id, WorkerRateCreateRequest(daily_rate=150_000, effective_from="2026-01-01")
    )
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)

    result = await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    row = next(r for r in result.data if r.worker_id == worker.id)
    assert row.trade == "철거"


async def test_get_month_returns_stored_results(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_active_worker(db_session)
    await rate_service.create_rate(
        db_session, worker.id, actor_id, WorkerRateCreateRequest(daily_rate=150_000, effective_from="2026-01-01")
    )
    await _record_attendance(db_session, actor_id, site_id, worker.id, PRESENT_DATES)
    await payroll_service.recalculate_month(db_session, TARGET_YEAR, TARGET_MONTH)

    listed = await payroll_service.get_month(db_session, TARGET_YEAR, TARGET_MONTH)

    row = next(r for r in listed.data if r.worker_id == worker.id)
    assert row.calc_status == "ok"
    assert row.target_month == date(2026, 7, 1)
