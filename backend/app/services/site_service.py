"""현장(프로젝트) 등록/조회/수정/삭제."""

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, SiteInUseError
from app.models.site import Site
from app.repositories import site_repository, worker_repository
from app.schemas.common import CursorPage
from app.schemas.site import (
    SiteCreateRequest,
    SiteListResponse,
    SiteResponse,
    SiteTradeListResponse,
    SiteUpdateRequest,
)


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


async def update_site(db: AsyncSession, site_id: UUID, payload: SiteUpdateRequest) -> SiteResponse:
    site = await site_repository.get_site_by_id(db, site_id)
    if site is None:
        raise NotFoundError(f"현장을 찾을 수 없습니다: {site_id}")

    if payload.name is not None:
        site.name = payload.name
    if payload.client_name is not None:
        site.client_name = payload.client_name
    if payload.start_date is not None:
        site.start_date = payload.start_date

    await db.flush()
    await db.refresh(site)
    return SiteResponse.model_validate(site)


async def delete_site(db: AsyncSession, site_id: UUID) -> None:
    site = await site_repository.get_site_by_id(db, site_id)
    if site is None:
        raise NotFoundError(f"현장을 찾을 수 없습니다: {site_id}")

    try:
        await site_repository.delete_site(db, site)
        await db.flush()
    except IntegrityError as exc:
        raise SiteInUseError("이 현장에 연결된 근로자 또는 출역 기록이 있어 삭제할 수 없습니다.") from exc
