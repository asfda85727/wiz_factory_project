"""월별 계산 결과 데이터 접근 + 계산에 필요한 출역/단가 조회."""

from datetime import date
from uuid import UUID

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord
from app.models.payroll_result import PayrollResult
from app.models.worker_rate import WorkerRate


async def list_present_worker_ids_for_month(
    db: AsyncSession, month_start: date, month_end: date
) -> list[UUID]:
    stmt = (
        select(AttendanceRecord.worker_id)
        .where(
            AttendanceRecord.is_present.is_(True),
            AttendanceRecord.work_date >= month_start,
            AttendanceRecord.work_date <= month_end,
        )
        .distinct()
    )
    return list((await db.execute(stmt)).scalars().all())


async def count_present_days(db: AsyncSession, worker_id: UUID, month_start: date, month_end: date) -> int:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.worker_id == worker_id,
        AttendanceRecord.is_present.is_(True),
        AttendanceRecord.work_date >= month_start,
        AttendanceRecord.work_date <= month_end,
    )
    return len((await db.execute(stmt)).scalars().all())


async def find_rate_for_month(
    db: AsyncSession, worker_id: UUID, month_start: date, month_end: date
) -> WorkerRate | None:
    stmt = select(WorkerRate).where(
        WorkerRate.worker_id == worker_id,
        WorkerRate.effective_from <= month_end,
        or_(WorkerRate.effective_to.is_(None), WorkerRate.effective_to >= month_start),
    )
    return (await db.execute(stmt)).scalars().first()


async def get_by_worker_and_month(db: AsyncSession, worker_id: UUID, target_month: date) -> PayrollResult | None:
    stmt = select(PayrollResult).where(
        PayrollResult.worker_id == worker_id, PayrollResult.target_month == target_month
    )
    return (await db.execute(stmt)).scalars().first()


async def list_by_month(db: AsyncSession, target_month: date) -> list[PayrollResult]:
    stmt = (
        select(PayrollResult)
        .where(PayrollResult.target_month == target_month)
        .order_by(PayrollResult.worker_id)
    )
    return list((await db.execute(stmt)).scalars().all())


async def delete_results_except(
    db: AsyncSession, target_month: date, keep_worker_ids: list[UUID]
) -> None:
    """재계산 대상(출역 있는 근로자)이 아닌, 그 달의 잔존 결과를 삭제한다.

    출역 기록이 지워지거나 옮겨져 더 이상 그 달에 출역이 없는 근로자의 payroll_results가
    남아 명세서에 유령처럼 계속 뜨는 문제를 막는다.
    """
    stmt = delete(PayrollResult).where(PayrollResult.target_month == target_month)
    if keep_worker_ids:
        stmt = stmt.where(PayrollResult.worker_id.not_in(keep_worker_ids))
    await db.execute(stmt)
