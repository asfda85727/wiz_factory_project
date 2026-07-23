"""관리자 로그인. 구글/MS ID 토큰을 검증해 이메일을 얻고, 화이트리스트(users 테이블)에
있는 이메일이면 자체 세션 JWT를 발급한다. 근로자 셀프 로그인(OTP)은 별도 기능으로 범위 밖."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth import create_access_token
from app.core.exceptions import UnauthorizedError
from app.core.oauth import OidcProviderConfig, google_provider_config, microsoft_provider_config, verify_id_token
from app.repositories import user_repository
from app.schemas.auth import AdminLoginResponse, OidcLoginRequest


async def _login_with_provider(
    db: AsyncSession, payload: OidcLoginRequest, provider_config: OidcProviderConfig
) -> AdminLoginResponse:
    email = verify_id_token(payload.id_token, provider_config)

    user = await user_repository.get_user_by_email(db, email)
    if user is None:
        raise UnauthorizedError(f"등록되지 않은 관리자 이메일입니다: {email}")

    token = create_access_token(str(user.id), user.email)
    return AdminLoginResponse(access_token=token, expires_in_minutes=settings.jwt_expire_minutes)


async def login_with_google(db: AsyncSession, payload: OidcLoginRequest) -> AdminLoginResponse:
    return await _login_with_provider(db, payload, google_provider_config())


async def login_with_microsoft(db: AsyncSession, payload: OidcLoginRequest) -> AdminLoginResponse:
    return await _login_with_provider(db, payload, microsoft_provider_config())
