"""관리자 세션 JWT 발급/검증 단위테스트 (DB 불필요, 순수 함수)."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.config import settings
from app.core.auth import create_access_token, decode_access_token
from app.core.exceptions import UnauthorizedError


def test_create_and_decode_access_token_roundtrip():
    token = create_access_token(user_id="user-123", email="admin@example.com")

    context = decode_access_token(token)

    assert context.user_id == "user-123"
    assert context.email == "admin@example.com"


def test_decode_access_token_rejects_garbage_token():
    with pytest.raises(UnauthorizedError):
        decode_access_token("not-a-valid-jwt")


def test_decode_access_token_rejects_expired_token():
    now = datetime.now(timezone.utc)
    expired_payload = {
        "sub": "user-123",
        "email": "admin@example.com",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=1),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(UnauthorizedError):
        decode_access_token(expired_token)


def test_decode_access_token_rejects_wrong_secret():
    token = jwt.encode(
        {"sub": "user-123", "email": "admin@example.com", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        "a-different-secret",
        algorithm="HS256",
    )

    with pytest.raises(UnauthorizedError):
        decode_access_token(token)
