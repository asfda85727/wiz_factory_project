"""근로자. 주민등록번호/계좌번호는 암호화 저장 + 마스킹 컬럼을 별도로 둔다.

resident_reg_no_enc / bank_account_enc: AES-256-GCM 암호문(app.core.security).
*_masked: 화면 표시용 — 쓰기 시점에 한 번만 계산해 저장, 조회 시 복호화가 필요 없도록 한다.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, LargeBinary, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Worker(Base):
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="provisional", index=True)
    trade: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    resident_reg_no_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    resident_registration_number_masked: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_account_enc: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    bank_account_masked: Mapped[str | None] = mapped_column(String(30), nullable=True)

    id_scan_file_key: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bankbook_scan_file_key: Mapped[str | None] = mapped_column(String(300), nullable=True)

    current_site_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sites.id", ondelete="RESTRICT"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
