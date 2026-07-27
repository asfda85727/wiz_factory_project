"""PDF 출역 명단 미리보기: 기존/신규/동명이인/현장다름/공정다름/삭제예정 검증.

tests/fixtures/tbm_예시.pdf 실제 샘플을 사용 — 1페이지(2025-09-10) "관리자" 열에
"박상용"이 등장한다.
"""

from datetime import date
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.attendance import AttendanceDailySaveRequest, AttendanceEntryInput
from app.schemas.worker import WorkerCreateRequest
from app.services import attendance_pdf_service, attendance_service, worker_service
from app.services.attendance_pdf_parser import ParsedEntry
from app.services.attendance_pdf_service import _build_row

SAMPLE_PDF = (Path(__file__).parent / "fixtures" / "tbm_예시.pdf").read_bytes()
DAY1 = date(2025, 9, 10)


async def _create_worker(db_session: AsyncSession, name: str, trade: str | None = None, site_id=None):
    return await worker_service.create_worker(
        db_session,
        WorkerCreateRequest(name=name, birth_date=date(1985, 3, 15), trade=trade, current_site_id=site_id),
    )


async def test_unmatched_name_is_new(db_session: AsyncSession, site_id):
    # 실제 PDF 샘플의 이름(예: 박상용)은 실사용 중 실제로 등록됐을 수 있어 "미등록 상태"를
    # 보장할 수 없다 — DB에 존재하지 않음이 확실한 합성 이름으로 매칭 로직만 독립적으로 검증.
    entry = ParsedEntry(work_date=DAY1, trade="관리자", name="존재하지않는이름_테스트용", column_index=1)

    row = await _build_row(db_session, site_id, entry)

    assert row.is_new is True
    assert row.matched_worker_id is None


async def test_matched_worker_no_mismatch_when_trade_and_site_agree(db_session: AsyncSession, site_id):
    worker = await _create_worker(db_session, "박상용", trade="관리자", site_id=site_id)

    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    row = next(r for r in result.rows if r.raw_name == "박상용")
    assert row.matched_worker_id == worker.id
    assert row.is_new is False
    assert row.trade_mismatch is False
    assert row.site_mismatch is False


async def test_trade_mismatch_flagged_but_not_overwritten(db_session: AsyncSession, site_id):
    await _create_worker(db_session, "박상용", trade="목수", site_id=site_id)

    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    row = next(r for r in result.rows if r.raw_name == "박상용")
    assert row.stored_trade == "목수"
    assert row.trade == "관리자"
    assert row.trade_mismatch is True


async def test_site_mismatch_flagged(db_session: AsyncSession, site_id, other_site_id):
    await _create_worker(db_session, "박상용", trade="관리자", site_id=other_site_id)

    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    row = next(r for r in result.rows if r.raw_name == "박상용")
    assert row.site_mismatch is True


async def test_duplicate_name_flagged(db_session: AsyncSession, site_id):
    await _create_worker(db_session, "박상용", trade="관리자")
    await _create_worker(db_session, "박상용", trade="관리자")

    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    row = next(r for r in result.rows if r.raw_name == "박상용")
    assert row.has_duplicate_name is True


async def test_to_be_removed_lists_existing_record_missing_from_pdf(
    db_session: AsyncSession, actor_id, site_id
):
    worker = await _create_worker(db_session, "테스트근로자아무개", trade="목수")
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=DAY1, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    removed_ids = {r.worker_id for r in result.to_be_removed if r.work_date == DAY1}
    assert worker.id in removed_ids


async def test_to_be_removed_excludes_worker_present_in_pdf(db_session: AsyncSession, actor_id, site_id):
    worker = await _create_worker(db_session, "박상용", trade="관리자", site_id=site_id)
    await attendance_service.save_daily(
        db_session,
        actor_id,
        AttendanceDailySaveRequest(
            site_id=site_id, work_date=DAY1, entries=[AttendanceEntryInput(worker_id=worker.id)]
        ),
    )

    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    removed_ids = {r.worker_id for r in result.to_be_removed if r.work_date == DAY1}
    assert worker.id not in removed_ids


async def test_skipped_pages_reported(db_session: AsyncSession, site_id):
    result = await attendance_pdf_service.preview(db_session, site_id, SAMPLE_PDF)

    assert len(result.skipped_pages) == 1
    assert result.skipped_pages[0].page_number == 3
