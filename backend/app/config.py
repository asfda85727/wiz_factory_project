"""애플리케이션 설정. 필수 시크릿이 없거나 형식이 틀리면 기동 즉시 실패한다(security.md 원칙)."""

import base64

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str
    jwt_secret: str
    jwt_expire_minutes: int = 480
    encryption_key_base64: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "labor-cost-files"
    minio_secure: bool = False
    cors_allowed_origins: str = "http://localhost:5173"
    google_client_id: str
    microsoft_client_id: str

    @field_validator("encryption_key_base64")
    @classmethod
    def _validate_key_length(cls, value: str) -> str:
        decoded = base64.b64decode(value)
        if len(decoded) != 32:
            raise ValueError("ENCRYPTION_KEY_BASE64는 디코딩 시 정확히 32바이트여야 합니다 (AES-256).")
        return value


settings = Settings()
