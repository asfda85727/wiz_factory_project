"""관리자 계정. role은 전부 'admin' (기획서 4번 확정, 등급 구분 없음).

로그인은 구글/MS 계정으로만 하고(2026-07-20 결정), 이 테이블은 "이 이메일은 관리자다"라는
화이트리스트 역할만 한다 — 비밀번호는 저장하지 않는다.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
