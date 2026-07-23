"""현장(프로젝트) 목록/등록 라우터."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.db.session import get_db_session
from app.schemas.site import SiteCreateRequest, SiteListResponse, SiteResponse, SiteTradeListResponse
from app.services import site_service

router = APIRouter(prefix="/sites", tags=["Sites"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=SiteListResponse)
async def list_sites(
    cursor: str | None = None,
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db_session),
) -> SiteListResponse:
    return await site_service.list_sites(db, cursor, limit)


@router.post("", response_model=SiteResponse, status_code=201)
async def create_site(payload: SiteCreateRequest, db: AsyncSession = Depends(get_db_session)) -> SiteResponse:
    response = await site_service.create_site(db, payload)
    await db.commit()
    return response


@router.get("/{site_id}/trades", response_model=SiteTradeListResponse)
async def get_site_trades(site_id: UUID, db: AsyncSession = Depends(get_db_session)) -> SiteTradeListResponse:
    return await site_service.get_trades(db, site_id)
