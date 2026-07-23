"""근로자 현장 이동 이력 조회."""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.repositories import site_assignment_repository, worker_repository
from app.schemas.common import CursorPage
from app.schemas.worker import SiteAssignmentLogEntryResponse, SiteHistoryResponse


async def get_site_history(
    db: AsyncSession, worker_id: UUID, cursor: str | None, limit: int
) -> SiteHistoryResponse:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")

    rows, next_cursor, has_more = await site_assignment_repository.list_site_history(
        db, worker_id, cursor, limit
    )
    entries = [
        SiteAssignmentLogEntryResponse(
            id=log.id,
            site_id=log.site_id,
            site_name=site_name,
            assigned_from=log.assigned_from,
            assigned_to=log.assigned_to,
        )
        for log, site_name in rows
    ]
    return SiteHistoryResponse(data=entries, pagination=CursorPage(next_cursor=next_cursor, has_more=has_more))
