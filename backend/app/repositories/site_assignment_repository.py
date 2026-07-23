"""현장 이동 이력 데이터 접근. 최신순(assigned_from DESC), 현장명 조인 포함."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.models.site import Site
from app.models.site_assignment_log import SiteAssignmentLog


async def close_open_assignment(db: AsyncSession, worker_id: UUID, closed_on: date) -> None:
    await db.execute(
        update(SiteAssignmentLog)
        .where(SiteAssignmentLog.worker_id == worker_id, SiteAssignmentLog.assigned_to.is_(None))
        .values(assigned_to=closed_on)
    )


async def create_assignment(db: AsyncSession, worker_id: UUID, site_id: UUID, assigned_from: date) -> None:
    db.add(SiteAssignmentLog(worker_id=worker_id, site_id=site_id, assigned_from=assigned_from))


async def list_site_history(
    db: AsyncSession, worker_id: UUID, cursor: str | None, limit: int
) -> tuple[list[tuple[SiteAssignmentLog, str]], str | None, bool]:
    stmt = (
        select(SiteAssignmentLog, Site.name)
        .join(Site, Site.id == SiteAssignmentLog.site_id)
        .where(SiteAssignmentLog.worker_id == worker_id)
        .order_by(SiteAssignmentLog.assigned_from.desc(), SiteAssignmentLog.id.desc())
        .limit(limit + 1)
    )
    if cursor:
        cursor_date_str, cursor_id = decode_cursor(cursor)
        cursor_date = date.fromisoformat(cursor_date_str)
        stmt = stmt.where(
            or_(
                SiteAssignmentLog.assigned_from < cursor_date,
                and_(
                    SiteAssignmentLog.assigned_from == cursor_date,
                    SiteAssignmentLog.id < UUID(cursor_id),
                ),
            )
        )

    rows = list((await db.execute(stmt)).all())
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = (
        encode_cursor(page[-1][0].assigned_from.isoformat(), str(page[-1][0].id))
        if has_more and page
        else None
    )
    return page, next_cursor, has_more
