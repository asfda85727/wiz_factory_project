"""월별 계산 결과(세목별). target_month는 항상 해당 월 1일로 저장한다.

calc_status: 'ok' | 'held' — 기획서 6.4/10번: 임시 등록자(provisional)나 대상월에 적용할
단가가 없는 근로자는 'held'로 보류하고 세목 계산을 하지 않는다(잘못된 숫자를 내는 것보다 안전).
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PayrollResult(Base):
    __tablename__ = "payroll_results"
    __table_args__ = (UniqueConstraint("worker_id", "target_month", name="uq_payroll_worker_month"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_month: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    work_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    gross_pay: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    income_tax: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    local_tax: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    employment_insurance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    national_pension: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    health_insurance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    long_term_care: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    net_pay: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    calc_status: Mapped[str] = mapped_column(String(10), nullable=False, default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
