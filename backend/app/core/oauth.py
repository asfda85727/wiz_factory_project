"""관리자 로그인용 구글/MS ID 토큰 검증.

서버는 OAuth client secret이 필요 없다 — 프론트가 구글/MS SDK로 받은 ID 토큰(서명된 JWT)의
서명을 각 provider의 공개키(JWKS)로 검증하고 iss/aud/exp만 확인하면 되는 순수 OIDC 검증이기
때문이다. "누가 로그인했는지"만 확인하고, "그 이메일이 이 시스템 관리자인지"는
별도로 화이트리스트(users 테이블) 대조로 판단한다(app.services.auth_service).

MS 앱을 멀티테넌트(common)로 등록하면 iss에 실제 로그인한 계정의 테넌트 ID가 들어가 고정값
매칭이 안 되므로 패턴으로만 확인한다 — 최종 신뢰 경계는 어차피 이메일 화이트리스트다.
"""

import re
from dataclasses import dataclass

import jwt
from jwt import PyJWKClient

from app.config import settings
from app.core.exceptions import UnauthorizedError

GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUER_PATTERN = re.compile(r"^https://accounts\.google\.com$")

MICROSOFT_JWKS_URI = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
MICROSOFT_ISSUER_PATTERN = re.compile(r"^https://login\.microsoftonline\.com/[^/]+/v2\.0$")


@dataclass(frozen=True)
class OidcProviderConfig:
    name: str
    jwks_uri: str
    issuer_pattern: re.Pattern[str]
    audience: str


def google_provider_config() -> OidcProviderConfig:
    return OidcProviderConfig(
        name="google", jwks_uri=GOOGLE_JWKS_URI, issuer_pattern=GOOGLE_ISSUER_PATTERN, audience=settings.google_client_id
    )


def microsoft_provider_config() -> OidcProviderConfig:
    return OidcProviderConfig(
        name="microsoft",
        jwks_uri=MICROSOFT_JWKS_URI,
        issuer_pattern=MICROSOFT_ISSUER_PATTERN,
        audience=settings.microsoft_client_id,
    )


def verify_id_token(token: str, config: OidcProviderConfig, jwk_client: PyJWKClient | None = None) -> str:
    """ID 토큰 서명·발급자·대상을 검증하고 이메일을 반환한다. 실패 시 UnauthorizedError."""
    client = jwk_client or PyJWKClient(config.jwks_uri)
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, signing_key.key, algorithms=["RS256"], audience=config.audience)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError(f"{config.name} 로그인 토큰이 유효하지 않습니다.") from exc

    if not config.issuer_pattern.fullmatch(payload.get("iss", "")):
        raise UnauthorizedError(f"{config.name} 로그인 토큰 발급자가 올바르지 않습니다.")

    email = payload.get("email") or payload.get("preferred_username")
    if not email:
        raise UnauthorizedError(f"{config.name} 계정에서 이메일 정보를 확인할 수 없습니다.")
    if payload.get("email_verified") is False:
        raise UnauthorizedError("이메일 인증이 완료되지 않은 계정입니다.")

    return email
