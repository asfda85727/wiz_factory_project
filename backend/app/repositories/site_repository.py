"""현장(프로젝트) 데이터 접근."""

from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import decode_cursor, encode_cursor
from app.models.site import Site


async def list_sites(db: AsyncSession, cursor: str | None, limit: int) -> tuple[list[Site], str | None, bool]:
    stmt = select(Site).order_by(Site.name, Site.id).limit(limit + 1)
    if cursor:
        cursor_name, cursor_id = decode_cursor(cursor)
        stmt = stmt.where(
            or_(Site.name > cursor_name, and_(Site.name == cursor_name, Site.id > UUID(cursor_id)))
        )

    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    page = rows[:limit]
    next_cursor = encode_cursor(page[-1].name, str(page[-1].id)) if has_more and page else None
    return page, next_cursor, has_more


async def get_site_by_id(db: AsyncSession, site_id: UUID) -> Site | None:
    return await db.get(Site, site_id)


async def delete_site(db: AsyncSession, site: Site) -> None:
    await db.delete(site)


async def get_names_by_ids(db: AsyncSession, site_ids: list[UUID]) -> dict[UUID, str]:
    if not site_ids:
        return {}
    stmt = select(Site.id, Site.name).where(Site.id.in_(site_ids))
    return {row[0]: row[1] for row in (await db.execute(stmt)).all()}
