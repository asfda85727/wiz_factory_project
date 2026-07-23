"""현장 이동 이력. 근로자는 1인 1현장 원칙, 이동 시 기간 기록."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SiteAssignmentLog(Base):
    __tablename__ = "site_assignment_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    site_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assigned_from: Mapped[date] = mapped_column(Date, nullable=False)
    assigned_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
