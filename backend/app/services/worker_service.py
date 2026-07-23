"""근로자 마스터 비즈니스 로직: 등록/수정/조회 + PII 암호화·마스킹 + 정식전환 검증."""

from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, WorkerActivationIncompleteError
from app.core.security import encrypt_pii, mask_bank_account, mask_resident_registration_number
from app.models.worker import Worker
from app.repositories import site_assignment_repository, worker_repository
from app.schemas.common import CursorPage
from app.schemas.worker import (
    WorkerCreateRequest,
    WorkerListResponse,
    WorkerResponse,
    WorkerStatus,
    WorkerUpdateRequest,
)

_UPDATABLE_FIELDS = ("name", "birth_date", "trade", "phone", "address", "bank_name", "current_site_id")


def _to_response(worker: Worker) -> WorkerResponse:
    return WorkerResponse(
        id=worker.id,
        name=worker.name,
        birth_date=worker.birth_date,
        status=WorkerStatus(worker.status),
        trade=worker.trade,
        phone=worker.phone,
        address=worker.address,
        bank_name=worker.bank_name,
        resident_registration_number_masked=worker.resident_registration_number_masked,
        bank_account_masked=worker.bank_account_masked,
        id_scan_uploaded=worker.id_scan_file_key is not None,
        bankbook_scan_uploaded=worker.bankbook_scan_file_key is not None,
        current_site_id=worker.current_site_id,
        created_at=worker.created_at,
    )


def _apply_sensitive_fields(
    worker: Worker, resident_registration_number: str | None, bank_account_number: str | None
) -> None:
    if resident_registration_number:
        worker.resident_reg_no_enc = encrypt_pii(resident_registration_number)
        worker.resident_registration_number_masked = mask_resident_registration_number(
            resident_registration_number
        )
    if bank_account_number:
        worker.bank_account_enc = encrypt_pii(bank_account_number)
        worker.bank_account_masked = mask_bank_account(bank_account_number)


def _has_activation_requirements(worker: Worker, incoming: WorkerUpdateRequest) -> bool:
    birth_date = incoming.birth_date if incoming.birth_date is not None else worker.birth_date
    phone = incoming.phone if incoming.phone is not None else worker.phone
    has_resident_no = bool(incoming.resident_registration_number or worker.resident_reg_no_enc)
    has_bank_account = bool(incoming.bank_account_number or worker.bank_account_enc)
    return bool(birth_date) and bool(phone) and has_resident_no and has_bank_account


async def create_worker(db: AsyncSession, payload: WorkerCreateRequest) -> WorkerResponse:
    worker = Worker(
        name=payload.name,
        birth_date=payload.birth_date,
        trade=payload.trade,
        phone=payload.phone,
        address=payload.address,
        bank_name=payload.bank_name,
        current_site_id=payload.current_site_id,
        status=WorkerStatus.PROVISIONAL.value,
    )
    _apply_sensitive_fields(worker, payload.resident_registration_number, payload.bank_account_number)

    db.add(worker)
    await db.flush()

    if worker.current_site_id is not None:
        await site_assignment_repository.create_assignment(db, worker.id, worker.current_site_id, date.today())
        await db.flush()

    await db.refresh(worker)
    return _to_response(worker)


async def get_worker(db: AsyncSession, worker_id: UUID) -> WorkerResponse:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")
    return _to_response(worker)


async def update_worker(db: AsyncSession, worker_id: UUID, payload: WorkerUpdateRequest) -> WorkerResponse:
    worker = await worker_repository.get_worker_by_id(db, worker_id)
    if worker is None:
        raise NotFoundError(f"근로자를 찾을 수 없습니다: {worker_id}")

    if payload.status == WorkerStatus.ACTIVE and not _has_activation_requirements(worker, payload):
        raise WorkerActivationIncompleteError(
            "정식 전환에는 생년월일·전화번호·주민등록번호·계좌정보가 모두 필요합니다."
        )

    site_changed = payload.current_site_id is not None and payload.current_site_id != worker.current_site_id

    for field in _UPDATABLE_FIELDS:
        value = getattr(payload, field)
        if value is not None:
            setattr(worker, field, value)

    _apply_sensitive_fields(worker, payload.resident_registration_number, payload.bank_account_number)

    if site_changed:
        today = date.today()
        await site_assignment_repository.close_open_assignment(db, worker.id, today)
        await site_assignment_repository.create_assignment(db, worker.id, payload.current_site_id, today)

    if payload.status is not None:
        worker.status = payload.status.value

    await db.flush()
    await db.refresh(worker)
    return _to_response(worker)


async def list_workers(
    db: AsyncSession, search: str | None, status: str | None, cursor: str | None, limit: int
) -> WorkerListResponse:
    rows, next_cursor, has_more = await worker_repository.list_workers(db, search, status, cursor, limit)
    return WorkerListResponse(
        data=[_to_response(w) for w in rows],
        pagination=CursorPage(next_cursor=next_cursor, has_more=has_more),
    )
