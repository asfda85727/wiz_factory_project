"""일일 출역 입력 비즈니스 로직: 일괄저장/전일복사/개별수정(audit)/조회.

save_daily는 upsert가 아니라 reconcile이다 — 해당 site_id+work_date에 이미 저장된 기록 중
payload.entries에 없는 근로자는 삭제한다(화면에서 "제거" 후 저장하면 그대로 반영되도록).

근로자는 하루 1현장만 가능(DB UNIQUE(worker_id, work_date))하므로, 다른 현장에 이미 기록된
근로자를 오늘 이 현장 명단에 넣으려 하면 조용히 덮어쓰지 않고 AttendanceSiteConflictError로 막는다.

공정(trade)은 근로자가 프로젝트 기간 내내 고정으로 유지하는 값이라(근로자 마스터의 trade 필드),
출역 기록의 trade는 매번 그 시점의 worker.trade를 그대로 복사해 저장한다 — 출역 입력 화면에서
공정을 별도로 입력받지 않는다.
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AttendanceSiteConflictError, NotFoundError
from app.models.attendance_record import AttendanceRecord
from app.models.attendance_audit_log import AttendanceAuditLog
from app.repositories import attendance_repository, site_repository, worker_repository
from app.schemas.attendance import (
    AttendanceDailyResponse,
    AttendanceDailySaveRequest,
    AttendanceEntryInput,
    AttendanceListResponse,
    AttendanceRecordResponse,
    AttendanceSummary,
    WorkerAttendanceDayResponse,
    WorkerMonthlyAttendanceResponse,
)


def _summarize(responses: list[AttendanceRecordResponse]) -> AttendanceSummary:
    present = [r for r in responses if r.is_present]
    by_trade: dict[str, int] = {}
    for response in present:
        key = response.trade or "미분류"
        by_trade[key] = by_trade.get(key, 0) + 1
    return AttendanceSummary(total_count=len(responses), present_count=len(present), by_trade=by_trade)


def _to_response(record: AttendanceRecord, worker_name: str, trade: str | None) -> AttendanceRecordResponse:
    return AttendanceRecordResponse(
        id=record.id,
        worker_id=record.worker_id,
        worker_name=worker_name,
        site_id=record.site_id,
        work_date=record.work_date,
        trade=trade,
        is_present=record.is_present,
        recorded_by=record.recorded_by,
        recorded_at=record.recorded_at,
        updated_at=record.updated_at,
    )


async def _upsert_entry(
    db: AsyncSession, actor_id: UUID, site_id: UUID, work_date: date, entry: AttendanceEntryInput
) -> tuple[AttendanceRecord, str, str | None]:
    worker = await worker_repository.get_worker_by_id(db, entry.worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {entry.worker_id}")

    existing = await attendance_repository.get_by_worker_and_date(db, entry.worker_id, work_date)
    if existing is not None and existing.site_id != site_id:
        raise AttendanceSiteConflictError(
            f"{worker.name}님은 이미 {work_date}에 다른 현장으로 등록되어 있습니다."
        )

    if existing is not None:
        existing.trade = worker.trade
        existing.is_present = entry.is_present
        return existing, worker.name, worker.trade

    record = AttendanceRecord(
        worker_id=entry.worker_id,
        site_id=site_id,
        work_date=work_date,
        trade=worker.trade,
        is_present=entry.is_present,
        recorded_by=actor_id,
    )
    db.add(record)
    return record, worker.name, worker.trade


async def get_daily(
    db: AsyncSession, site_id: UUID, work_date: date, trade: str | None
) -> AttendanceDailyResponse:
    records = await attendance_repository.list_daily(db, site_id, work_date, trade)
    info = await worker_repository.get_name_trade_by_ids(db, [r.worker_id for r in records])
    responses = [_to_response(r, *info.get(r.worker_id, ("", None))) for r in records]
    return AttendanceDailyResponse(data=responses, summary=_summarize(responses))


async def save_daily(
    db: AsyncSession, actor_id: UUID, payload: AttendanceDailySaveRequest
) -> AttendanceDailyResponse:
    existing = await attendance_repository.list_by_site_and_date(db, payload.site_id, payload.work_date)
    incoming_worker_ids = {entry.worker_id for entry in payload.entries}
    removed = [record for record in existing if record.worker_id not in incoming_worker_ids]
    for record in removed:
        await attendance_repository.delete_record(db, record)
    if removed:
        await db.flush()

    saved = [
        await _upsert_entry(db, actor_id, payload.site_id, payload.work_date, entry) for entry in payload.entries
    ]
    await db.flush()
    for record, _, _ in saved:
        await db.refresh(record)
    responses = [_to_response(record, name, trade) for record, name, trade in saved]
    return AttendanceDailyResponse(data=responses, summary=_summarize(responses))


async def copy_previous(db: AsyncSession, actor_id: UUID, site_id: UUID, work_date: date) -> AttendanceDailyResponse:
    previous_date = work_date - timedelta(days=1)
    source_records = await attendance_repository.list_by_site_and_date(db, site_id, previous_date)
    if not source_records:
        raise NotFoundError(f"{previous_date}에 이 현장의 출역 기록이 없습니다.")

    entries = [AttendanceEntryInput(worker_id=r.worker_id, is_present=r.is_present) for r in source_records]
    return await save_daily(db, actor_id, AttendanceDailySaveRequest(site_id=site_id, work_date=work_date, entries=entries))


async def update_attendance(
    db: AsyncSession, actor_id: UUID, attendance_id: UUID, payload
) -> AttendanceRecordResponse:
    record = await attendance_repository.get_by_id(db, attendance_id)
    if record is None:
        raise NotFoundError(f"출역 기록을 찾을 수 없습니다: {attendance_id}")

    old_value = f"is_present={record.is_present}"

    if payload.is_present is not None:
        record.is_present = payload.is_present

    new_value = f"is_present={record.is_present}"
    db.add(AttendanceAuditLog(attendance_id=record.id, changed_by=actor_id, old_value=old_value, new_value=new_value))

    await db.flush()
    await db.refresh(record)
    worker = await worker_repository.get_worker_by_id(db, record.worker_id)
    return _to_response(record, worker.name if worker else "", worker.trade if worker else None)


async def get_monthly(db: AsyncSession, site_id: UUID, year: int, month: int) -> AttendanceListResponse:
    records = await attendance_repository.list_monthly(db, site_id, year, month)
    info = await worker_repository.get_name_trade_by_ids(db, [r.worker_id for r in records])
    return AttendanceListResponse(data=[_to_response(r, *info.get(r.worker_id, ("", None))) for r in records])


async def get_worker_monthly(
    db: AsyncSession, worker_id: UUID, year: int, month: int
) -> WorkerMonthlyAttendanceResponse:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")

    records = await attendance_repository.list_worker_month(db, worker_id, year, month)
    site_names = await site_repository.get_names_by_ids(db, [r.site_id for r in records])
    # 공정은 "근로자당 고정" 속성이므로 출역 기록의 스냅샷이 아니라 근로자의 현재 공정을 쓴다
    # (공정을 나중에 지정한 경우 과거 출역 기록의 빈 공정이 그대로 노출되는 문제 방지).
    days = [
        WorkerAttendanceDayResponse(
            work_date=r.work_date,
            site_id=r.site_id,
            site_name=site_names.get(r.site_id, ""),
            trade=worker.trade,
            is_present=r.is_present,
        )
        for r in records
    ]
    return WorkerMonthlyAttendanceResponse(
        worker_id=worker_id,
        worker_name=worker.name,
        present_days=sum(1 for d in days if d.is_present),
        data=days,
    )
