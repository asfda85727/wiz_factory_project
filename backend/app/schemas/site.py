"""현장(프로젝트) 요청/응답 스키마."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import CursorPage


class SiteCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    start_date: date


class SiteUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    client_name: str | None = Field(default=None, min_length=1)
    start_date: date | None = None


class SiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    client_name: str
    start_date: date
    created_at: datetime


class SiteListResponse(BaseModel):
    data: list[SiteResponse]
    pagination: CursorPage


class SiteTradeListResponse(BaseModel):
    data: list[str]
