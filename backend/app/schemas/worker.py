"""근로자 요청/응답 스키마.

resident_registration_number·bank_account_number는 쓰기 전용 입력이며 어떤 응답 모델에도
포함하지 않는다 — 응답에는 마스킹된 필드(*_masked)만 노출한다.
"""

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import CursorPage


class WorkerStatus(StrEnum):
    ACTIVE = "active"
    PROVISIONAL = "provisional"


class WorkerFileType(StrEnum):
    ID_SCAN = "id_scan"
    BANKBOOK_SCAN = "bankbook_scan"


class WorkerCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    birth_date: date | None = None
    trade: str | None = None
    phone: str | None = None
    address: str | None = None
    bank_name: str | None = None
    resident_registration_number: str | None = None
    bank_account_number: str | None = None
    current_site_id: UUID | None = None


class WorkerUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    birth_date: date | None = None
    status: WorkerStatus | None = None
    trade: str | None = None
    phone: str | None = None
    address: str | None = None
    bank_name: str | None = None
    resident_registration_number: str | None = None
    bank_account_number: str | None = None
    current_site_id: UUID | None = None


class WorkerResponse(BaseModel):
    id: UUID
    name: str
    birth_date: date | None
    status: WorkerStatus
    trade: str | None
    phone: str | None
    address: str | None
    bank_name: str | None
    resident_registration_number_masked: str | None
    bank_account_masked: str | None
    id_scan_uploaded: bool
    bankbook_scan_uploaded: bool
    current_site_id: UUID | None
    created_at: datetime


class WorkerListResponse(BaseModel):
    data: list[WorkerResponse]
    pagination: CursorPage


class WorkerFileUploadResult(BaseModel):
    type: WorkerFileType
    uploaded_at: datetime


class SiteAssignmentLogEntryResponse(BaseModel):
    id: UUID
    site_id: UUID
    site_name: str
    assigned_from: date
    assigned_to: date | None


class SiteHistoryResponse(BaseModel):
    data: list[SiteAssignmentLogEntryResponse]
    pagination: CursorPage
