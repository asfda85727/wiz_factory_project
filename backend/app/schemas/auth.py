"""관리자 로그인 요청/응답. 로그인은 구글/MS ID 토큰으로만 한다."""

from pydantic import BaseModel


class OidcLoginRequest(BaseModel):
    id_token: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
