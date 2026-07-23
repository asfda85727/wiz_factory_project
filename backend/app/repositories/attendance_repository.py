"""출역 기록 데이터 접근."""

from datetime import date
from uuid import UUID

from sqlalchemy import extract, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance_record import AttendanceRecord


async def list_daily(
    db: AsyncSession, site_id: UUID, work_date: date, trade: str | None
) -> list[AttendanceRecord]:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.site_id == site_id, AttendanceRecord.work_date == work_date
    )
    if trade:
        stmt = stmt.where(AttendanceRecord.trade == trade)
    stmt = stmt.order_by(AttendanceRecord.worker_id)
    return list((await db.execute(stmt)).scalars().all())


async def list_by_site_and_date(db: AsyncSession, site_id: UUID, work_date: date) -> list[AttendanceRecord]:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.site_id == site_id, AttendanceRecord.work_date == work_date
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_monthly(db: AsyncSession, site_id: UUID, year: int, month: int) -> list[AttendanceRecord]:
    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.site_id == site_id,
            extract("year", AttendanceRecord.work_date) == year,
            extract("month", AttendanceRecord.work_date) == month,
        )
        .order_by(AttendanceRecord.work_date, AttendanceRecord.worker_id)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_worker_month(
    db: AsyncSession, worker_id: UUID, year: int, month: int
) -> list[AttendanceRecord]:
    stmt = (
        select(AttendanceRecord)
        .where(
            AttendanceRecord.worker_id == worker_id,
            extract("year", AttendanceRecord.work_date) == year,
            extract("month", AttendanceRecord.work_date) == month,
        )
        .order_by(AttendanceRecord.work_date)
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_by_worker_and_date(
    db: AsyncSession, worker_id: UUID, work_date: date
) -> AttendanceRecord | None:
    stmt = select(AttendanceRecord).where(
        AttendanceRecord.worker_id == worker_id, AttendanceRecord.work_date == work_date
    )
    return (await db.execute(stmt)).scalars().first()


async def get_by_id(db: AsyncSession, attendance_id: UUID) -> AttendanceRecord | None:
    return await db.get(AttendanceRecord, attendance_id)


async def delete_record(db: AsyncSession, record: AttendanceRecord) -> None:
    await db.delete(record)
