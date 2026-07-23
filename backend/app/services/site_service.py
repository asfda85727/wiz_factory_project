"""현장(프로젝트) 등록/조회."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site import Site
from app.repositories import site_repository, worker_repository
from app.schemas.common import CursorPage
from app.schemas.site import SiteCreateRequest, SiteListResponse, SiteResponse, SiteTradeListResponse


async def create_site(db: AsyncSession, payload: SiteCreateRequest) -> SiteResponse:
    site = Site(name=payload.name, client_name=payload.client_name, start_date=payload.start_date)
    db.add(site)
    await db.flush()
    await db.refresh(site)
    return SiteResponse.model_validate(site)


async def list_sites(db: AsyncSession, cursor: str | None, limit: int) -> SiteListResponse:
    rows, next_cursor, has_more = await site_repository.list_sites(db, cursor, limit)
    return SiteListResponse(
        data=[SiteResponse.model_validate(s) for s in rows],
        pagination=CursorPage(next_cursor=next_cursor, has_more=has_more),
    )


async def get_trades(db: AsyncSession, site_id: UUID) -> SiteTradeListResponse:
    trades = await worker_repository.list_distinct_trades_for_site(db, site_id)
    return SiteTradeListResponse(data=trades)
