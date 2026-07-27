"""출역 요청/응답 스키마."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AttendanceEntryInput(BaseModel):
    worker_id: UUID
    is_present: bool = True


class AttendanceDailySaveRequest(BaseModel):
    site_id: UUID
    work_date: date
    entries: list[AttendanceEntryInput] = Field(default_factory=list)


class AttendanceUpdateRequest(BaseModel):
    is_present: bool | None = None
    work_date: date | None = None
    site_id: UUID | None = None


class AttendanceRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    worker_id: UUID
    worker_name: str
    site_id: UUID
    work_date: date
    trade: str | None
    is_present: bool
    recorded_by: UUID
    recorded_at: datetime
    updated_at: datetime


class AttendanceSummary(BaseModel):
    total_count: int
    present_count: int
    by_trade: dict[str, int]


class AttendanceDailyResponse(BaseModel):
    data: list[AttendanceRecordResponse]
    summary: AttendanceSummary


class AttendanceListResponse(BaseModel):
    data: list[AttendanceRecordResponse]


class WorkerAttendanceDayResponse(BaseModel):
    """근로자 한 명의 하루 출역 — 현장을 넘나든 이력을 보여주므로 현장명을 포함한다."""

    id: UUID
    work_date: date
    site_id: UUID
    site_name: str
    trade: str | None
    is_present: bool


class WorkerMonthlyAttendanceResponse(BaseModel):
    worker_id: UUID
    worker_name: str
    present_days: int
    data: list[WorkerAttendanceDayResponse]


class PdfPreviewRow(BaseModel):
    work_date: date
    trade: str
    column_index: int
    raw_name: str
    matched_worker_id: UUID | None
    matched_worker_name: str | None
    is_new: bool
    has_duplicate_name: bool
    site_mismatch: bool
    stored_trade: str | None
    trade_mismatch: bool


class PdfRemovedEntry(BaseModel):
    work_date: date
    worker_id: UUID
    worker_name: str


class PdfSkippedPage(BaseModel):
    page_number: int
    reason: str


class PdfPreviewResponse(BaseModel):
    rows: list[PdfPreviewRow]
    to_be_removed: list[PdfRemovedEntry]
    skipped_pages: list[PdfSkippedPage]
