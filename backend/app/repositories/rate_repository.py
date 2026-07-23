"""근로자 단가 데이터 접근. 목록은 유효기간 최신순(effective_from DESC), 겹침 조회 포함."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.models.worker_rate import WorkerRate


async def list_worker_rates(
    db: AsyncSession, worker_id: UUID, cursor: str | None, limit: int
) -> tuple[list[WorkerRate], str | None, bool]:
    stmt = (
        select(WorkerRate)
        .where(WorkerRate.worker_id == worker_id)
        .order_by(WorkerRate.effective_from.desc(), WorkerRate.id.desc())
        .limit(limit + 1)
    )
    if cursor:
        cursor_date_str, cursor_id = decode_cursor(cursor)
        cursor_date = date.fromisoformat(cursor_date_str)
        stmt = stmt.where(
            or_(
                WorkerRate.effective_from < cursor_date,
                and_(WorkerRate.effective_from == cursor_date, WorkerRate.id < UUID(cursor_id)),
            )
        )

    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = (
        encode_cursor(page[-1].effective_from.isoformat(), str(page[-1].id)) if has_more and page else None
    )
    return page, next_cursor, has_more


async def find_overlapping_rate(
    db: AsyncSession,
    worker_id: UUID,
    effective_from: date,
    effective_to: date | None,
    exclude_rate_id: UUID | None = None,
) -> WorkerRate | None:
    stmt = select(WorkerRate).where(WorkerRate.worker_id == worker_id)
    if exclude_rate_id:
        stmt = stmt.where(WorkerRate.id != exclude_rate_id)

    conditions = []
    if effective_to is not None:
        conditions.append(WorkerRate.effective_from <= effective_to)
    conditions.append(or_(WorkerRate.effective_to.is_(None), WorkerRate.effective_to >= effective_from))
    stmt = stmt.where(and_(*conditions)).limit(1)

    result = await db.execute(stmt)
    return result.scalars().first()


async def get_rate_by_id(db: AsyncSession, rate_id: UUID) -> WorkerRate | None:
    return await db.get(WorkerRate, rate_id)
