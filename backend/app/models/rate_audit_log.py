"""단가 등록/변경 감사 로그. 등록·수정 시 항상 한 건씩 기록한다."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RateAuditLog(Base):
    __tablename__ = "rate_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_rates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    changed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    old_value: Mapped[str | None] = mapped_column(String(500), nullable=True)
    new_value: Mapped[str] = mapped_column(String(500), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
