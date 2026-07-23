"""관리자 로그인 라우터. 구글/MS 계정으로만 로그인한다(비밀번호 로그인 없음)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.auth import AdminLoginResponse, OidcLoginRequest
from app.services import auth_service

router = APIRouter(prefix="/admin", tags=["Auth"])


@router.post("/login/google", response_model=AdminLoginResponse)
async def login_google(
    payload: OidcLoginRequest, db: AsyncSession = Depends(get_db_session)
) -> AdminLoginResponse:
    return await auth_service.login_with_google(db, payload)


@router.post("/login/microsoft", response_model=AdminLoginResponse)
async def login_microsoft(
    payload: OidcLoginRequest, db: AsyncSession = Depends(get_db_session)
) -> AdminLoginResponse:
    return await auth_service.login_with_microsoft(db, payload)
