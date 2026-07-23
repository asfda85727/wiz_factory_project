"""관리자 세션 JWT(자체 발급) 발급/검증.

로그인 자체는 구글/MS OAuth로 하고(app.core.oauth), 그 결과 확인된 관리자에게
이 모듈이 세션용 JWT를 발급한다. 근로자 셀프 로그인(전화번호+주민번호+OTP)은
별도 기능으로 이 모듈 범위 밖이다.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.core.exceptions import UnauthorizedError

_bearer_scheme = HTTPBearer()


@dataclass(frozen=True)
class AdminContext:
    user_id: str
    email: str


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> AdminContext:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("인증 토큰이 유효하지 않거나 만료되었습니다.") from exc
    return AdminContext(user_id=payload["sub"], email=payload["email"])


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> AdminContext:
    return decode_access_token(credentials.credentials)
