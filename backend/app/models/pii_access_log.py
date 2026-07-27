"""개인정보(주민등록번호·계좌번호·신분증/통장 사본) 접근·변경 감사 로그.

개인정보보호법상 접근기록 보관을 위해, 누가(actor_id) 언제(at) 어떤 근로자(worker_id)의
개인정보를 어떤 식으로(action) 처리했는지 남긴다. 조회 화면은 마스킹만 보여주므로 기록
대상이 아니고, 평문이 개입하는 지점(입력·수정)과 사본 파일 접근(업로드·다운로드)만 남긴다.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PiiAccessLog(Base):
    __tablename__ = "pii_access_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    detail: Mapped[str | None] = mapped_column(String(200), nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
