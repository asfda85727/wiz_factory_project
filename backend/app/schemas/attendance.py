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
