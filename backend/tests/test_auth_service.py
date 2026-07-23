"""관리자 로그인 서비스: 화이트리스트 대조 + 세션 토큰 발급. 구글/MS 실제 검증은 test_oauth.py에서
다루므로, 여기서는 verify_id_token을 이메일만 돌려주는 스텁으로 대체해 whitelist 로직만 검증한다."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.models.user import User
from app.schemas.auth import OidcLoginRequest
from app.services import auth_service


async def _add_whitelisted_admin(db_session: AsyncSession, email: str) -> None:
    db_session.add(User(email=email, name="테스트 관리자"))
    await db_session.flush()


async def test_login_with_google_issues_token_for_whitelisted_email(db_session: AsyncSession, monkeypatch):
    await _add_whitelisted_admin(db_session, "admin@example.com")
    monkeypatch.setattr(auth_service, "verify_id_token", lambda token, config: "admin@example.com")

    response = await auth_service.login_with_google(db_session, OidcLoginRequest(id_token="fake-token"))

    assert response.access_token
    assert response.token_type == "bearer"


async def test_login_with_google_rejects_non_whitelisted_email(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(auth_service, "verify_id_token", lambda token, config: "stranger@example.com")

    with pytest.raises(UnauthorizedError):
        await auth_service.login_with_google(db_session, OidcLoginRequest(id_token="fake-token"))


async def test_login_with_microsoft_issues_token_for_whitelisted_email(db_session: AsyncSession, monkeypatch):
    await _add_whitelisted_admin(db_session, "admin@company.com")
    monkeypatch.setattr(auth_service, "verify_id_token", lambda token, config: "admin@company.com")

    response = await auth_service.login_with_microsoft(db_session, OidcLoginRequest(id_token="fake-token"))

    assert response.access_token


async def test_login_with_microsoft_rejects_non_whitelisted_email(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(auth_service, "verify_id_token", lambda token, config: "stranger@company.com")

    with pytest.raises(UnauthorizedError):
        await auth_service.login_with_microsoft(db_session, OidcLoginRequest(id_token="fake-token"))
