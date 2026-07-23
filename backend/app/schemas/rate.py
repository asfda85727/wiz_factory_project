"""근로자 단가 요청/응답 스키마."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import CursorPage


class WorkerRateCreateRequest(BaseModel):
    daily_rate: int = Field(ge=0)
    effective_from: date
    effective_to: date | None = None


class WorkerRateUpdateRequest(BaseModel):
    daily_rate: int | None = Field(default=None, ge=0)
    effective_to: date | None = None


class WorkerRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    worker_id: UUID
    daily_rate: int
    effective_from: date
    effective_to: date | None
    created_by: UUID
    created_at: datetime


class WorkerRateListResponse(BaseModel):
    data: list[WorkerRateResponse]
    pagination: CursorPage
