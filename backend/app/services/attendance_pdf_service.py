"""PDF 출역 명단 업로드 미리보기 (기획서 12번 8번). 조회 전용 — DB에 쓰지 않는다.

저장(확정)은 새 엔드포인트를 두지 않고, 프론트에서 기존
`POST /workers`, `PATCH /workers/{id}`, `POST /attendance/daily`를
순서대로 호출해 처리한다(이 모듈은 그 호출에 필요한 미리보기 정보만 만든다).

출역 저장(`save_daily`)은 그 현장+날짜에 없는 기존 기록을 삭제하는 reconcile이라,
PDF의 특정 공정 열이 인식되지 않으면 그 근로자들의 기존 출역이 티 안 나게 삭제될
위험이 있다 — 그래서 미리보기에 "이번 PDF에 없어서 삭제될 기존 기록"도 반드시 계산해 보여준다.
"""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import attendance_repository, worker_repository
from app.schemas.attendance import (
    PdfPreviewResponse,
    PdfPreviewRow,
    PdfRemovedEntry,
    PdfSkippedPage,
)
from app.services.attendance_pdf_parser import ParsedEntry, parse_attendance_pdf


async def preview(db: AsyncSession, site_id: UUID, pdf_bytes: bytes) -> PdfPreviewResponse:
    parsed = parse_attendance_pdf(pdf_bytes)

    rows = [await _build_row(db, site_id, entry) for entry in parsed.entries]
    to_be_removed = await _compute_to_be_removed(db, site_id, rows)
    skipped_pages = [PdfSkippedPage(page_number=p.page_number, reason=p.reason) for p in parsed.skipped_pages]

    return PdfPreviewResponse(rows=rows, to_be_removed=to_be_removed, skipped_pages=skipped_pages)


async def _build_row(db: AsyncSession, site_id: UUID, entry: ParsedEntry) -> PdfPreviewRow:
    candidates = await worker_repository.get_by_exact_name(db, entry.name, preferred_site_id=site_id)

    if not candidates:
        return PdfPreviewRow(
            work_date=entry.work_date,
            trade=entry.trade,
            column_index=entry.column_index,
            raw_name=entry.name,
            matched_worker_id=None,
            matched_worker_name=None,
            is_new=True,
            has_duplicate_name=False,
            site_mismatch=False,
            stored_trade=None,
            trade_mismatch=False,
        )

    matched = candidates[0]
    return PdfPreviewRow(
        work_date=entry.work_date,
        trade=entry.trade,
        column_index=entry.column_index,
        raw_name=entry.name,
        matched_worker_id=matched.id,
        matched_worker_name=matched.name,
        is_new=False,
        has_duplicate_name=len(candidates) > 1,
        site_mismatch=matched.current_site_id is not None and matched.current_site_id != site_id,
        stored_trade=matched.trade,
        trade_mismatch=matched.trade is not None and matched.trade != entry.trade,
    )


async def _compute_to_be_removed(
    db: AsyncSession, site_id: UUID, rows: list[PdfPreviewRow]
) -> list[PdfRemovedEntry]:
    resolved_ids_by_date: dict[date, set[UUID]] = {}
    dates: set[date] = set()
    for row in rows:
        dates.add(row.work_date)
        if row.matched_worker_id is not None:
            resolved_ids_by_date.setdefault(row.work_date, set()).add(row.matched_worker_id)

    removed: list[PdfRemovedEntry] = []
    for work_date in sorted(dates):
        existing_records = await attendance_repository.list_by_site_and_date(db, site_id, work_date)
        resolved_ids = resolved_ids_by_date.get(work_date, set())
        missing = [record for record in existing_records if record.worker_id not in resolved_ids]
        if not missing:
            continue
        names = await worker_repository.get_names_by_ids(db, [record.worker_id for record in missing])
        for record in missing:
            removed.append(
                PdfRemovedEntry(
                    work_date=work_date,
                    worker_id=record.worker_id,
                    worker_name=names.get(record.worker_id, ""),
                )
            )
    return removed
