"""구글/MS ID 토큰 검증 단위테스트. 실제 구글/MS 서버에 붙지 않고, 테스트용 RSA 키로 서명한
토큰 + JWKS 클라이언트를 흉내낸 스텁으로 검증 로직만 확인한다."""

import re
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.oauth import OidcProviderConfig, google_provider_config, microsoft_provider_config, verify_id_token

_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_PUBLIC_KEY = _PRIVATE_KEY.public_key()

TEST_CONFIG = OidcProviderConfig(
    name="test-provider",
    jwks_uri="https://example.invalid/jwks",
    issuer_pattern=re.compile(r"^https://issuer\.example\.com$"),
    audience="test-client-id",
)


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJwkClient:
    def get_signing_key_from_jwt(self, token: str) -> _FakeSigningKey:
        return _FakeSigningKey(_PUBLIC_KEY)


def _build_token(claims: dict) -> str:
    payload = {
        "iss": "https://issuer.example.com",
        "aud": "test-client-id",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "email": "admin@example.com",
        **claims,
    }
    return jwt.encode(payload, _PRIVATE_KEY, algorithm="RS256")


def test_verify_id_token_returns_email_for_valid_token():
    token = _build_token({})

    email = verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())

    assert email == "admin@example.com"


def test_verify_id_token_rejects_wrong_audience():
    token = _build_token({"aud": "someone-elses-client-id"})

    with pytest.raises(UnauthorizedError):
        verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())


def test_verify_id_token_rejects_wrong_issuer():
    token = _build_token({"iss": "https://not-the-real-issuer.example.com"})

    with pytest.raises(UnauthorizedError):
        verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())


def test_verify_id_token_rejects_expired_token():
    token = _build_token({"exp": datetime.now(timezone.utc) - timedelta(minutes=1)})

    with pytest.raises(UnauthorizedError):
        verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())


def test_verify_id_token_rejects_missing_email():
    token = _build_token({"email": None})

    with pytest.raises(UnauthorizedError):
        verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())


def test_verify_id_token_falls_back_to_preferred_username():
    token = _build_token({"email": None, "preferred_username": "user@company.com"})

    email = verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())

    assert email == "user@company.com"


def test_verify_id_token_rejects_unverified_email():
    token = _build_token({"email_verified": False})

    with pytest.raises(UnauthorizedError):
        verify_id_token(token, TEST_CONFIG, jwk_client=_FakeJwkClient())


def test_microsoft_issuer_pattern_accepts_any_tenant():
    config = OidcProviderConfig(
        name="microsoft",
        jwks_uri="https://example.invalid/jwks",
        issuer_pattern=microsoft_provider_config().issuer_pattern,
        audience="test-client-id",
    )
    token = jwt.encode(
        {
            "iss": "https://login.microsoftonline.com/some-tenant-guid/v2.0",
            "aud": "test-client-id",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
            "email": "admin@company.com",
        },
        _PRIVATE_KEY,
        algorithm="RS256",
    )

    email = verify_id_token(token, config, jwk_client=_FakeJwkClient())

    assert email == "admin@company.com"


def test_google_provider_config_reads_client_id_from_settings():
    assert google_provider_config().audience == settings.google_client_id


def test_microsoft_provider_config_reads_client_id_from_settings():
    assert microsoft_provider_config().audience == settings.microsoft_client_id
