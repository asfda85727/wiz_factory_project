"""근로자 데이터 접근. 목록 커서는 (name, id) 키셋 방식(전체검색 자동완성이라 이름순 정렬)."""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.models.worker import Worker


async def list_distinct_trades_for_site(db: AsyncSession, site_id: UUID) -> list[str]:
    stmt = (
        select(Worker.trade)
        .where(Worker.current_site_id == site_id, Worker.trade.is_not(None))
        .distinct()
        .order_by(Worker.trade)
    )
    return [row[0] for row in (await db.execute(stmt)).all()]


async def list_workers(
    db: AsyncSession,
    search: str | None,
    status: str | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[Worker], str | None, bool]:
    stmt = select(Worker).order_by(Worker.name, Worker.id).limit(limit + 1)

    if search:
        stmt = stmt.where(Worker.name.ilike(f"%{search}%"))
    if status:
        stmt = stmt.where(Worker.status == status)
    if cursor:
        cursor_name, cursor_id = decode_cursor(cursor)
        stmt = stmt.where(
            or_(
                Worker.name > cursor_name,
                and_(Worker.name == cursor_name, Worker.id > UUID(cursor_id)),
            )
        )

    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1].name, str(page[-1].id)) if has_more and page else None
    return page, next_cursor, has_more


async def get_worker_by_id(db: AsyncSession, worker_id: UUID) -> Worker | None:
    return await db.get(Worker, worker_id)


async def get_names_by_ids(db: AsyncSession, worker_ids: list[UUID]) -> dict[UUID, str]:
    if not worker_ids:
        return {}
    stmt = select(Worker.id, Worker.name).where(Worker.id.in_(worker_ids))
    return {row[0]: row[1] for row in (await db.execute(stmt)).all()}


async def get_name_trade_by_ids(
    db: AsyncSession, worker_ids: list[UUID]
) -> dict[UUID, tuple[str, str | None]]:
    if not worker_ids:
        return {}
    stmt = select(Worker.id, Worker.name, Worker.trade).where(Worker.id.in_(worker_ids))
    return {row[0]: (row[1], row[2]) for row in (await db.execute(stmt)).all()}
