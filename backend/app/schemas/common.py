"""공통 응답 스키마."""

from pydantic import BaseModel


class CursorPage(BaseModel):
    next_cursor: str | None
    has_more: bool
