"""월별 계산 결과 응답 스키마."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PayrollResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    worker_id: UUID
    worker_name: str
    trade: str | None
    site_id: UUID | None
    site_name: str | None
    target_month: date
    work_days: int
    gross_pay: int
    income_tax: int
    local_tax: int
    employment_insurance: int
    national_pension: int
    health_insurance: int
    long_term_care: int
    net_pay: int
    calc_status: str
    created_at: datetime
    updated_at: datetime


class PayrollListResponse(BaseModel):
    data: list[PayrollResultResponse]
