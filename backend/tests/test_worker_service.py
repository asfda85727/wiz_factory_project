"""근로자 마스터 서비스: 정식전환 게이트, 현장이동이력 기록 검증."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, WorkerActivationIncompleteError
from app.repositories import site_assignment_repository
from app.schemas.worker import WorkerCreateRequest, WorkerStatus, WorkerUpdateRequest
from app.services import worker_service


async def _create_minimal_worker(db_session: AsyncSession):
    return await worker_service.create_worker(
        db_session, WorkerCreateRequest(name="김철수", birth_date="1985-03-15")
    )


async def test_create_worker_minimal_registers_as_provisional(db_session: AsyncSession):
    worker = await _create_minimal_worker(db_session)

    assert worker.status == WorkerStatus.PROVISIONAL
    assert worker.current_site_id is None


async def test_create_worker_name_only_registers_as_provisional(db_session: AsyncSession):
    worker = await worker_service.create_worker(db_session, WorkerCreateRequest(name="무명씨"))

    assert worker.status == WorkerStatus.PROVISIONAL
    assert worker.birth_date is None


async def test_activate_without_birth_date_raises(db_session: AsyncSession):
    worker = await worker_service.create_worker(db_session, WorkerCreateRequest(name="무명씨"))

    with pytest.raises(WorkerActivationIncompleteError):
        await worker_service.update_worker(
            db_session,
            worker.id,
            WorkerUpdateRequest(
                status=WorkerStatus.ACTIVE,
                phone="010-1234-5678",
                resident_registration_number="850315-1234567",
                bank_account_number="123-456-789",
            ),
        )


async def test_create_worker_with_site_opens_assignment_log(db_session: AsyncSession, site_id):
    worker = await worker_service.create_worker(
        db_session,
        WorkerCreateRequest(name="이영희", birth_date="1990-05-20", current_site_id=site_id),
    )

    rows, _, _ = await site_assignment_repository.list_site_history(db_session, worker.id, None, 20)
    assert len(rows) == 1
    log, site_name = rows[0]
    assert log.site_id == site_id
    assert log.assigned_to is None
    assert site_name == "테스트 현장"


async def test_get_worker_not_found_raises(db_session: AsyncSession):
    with pytest.raises(NotFoundError):
        await worker_service.get_worker(db_session, uuid4())


async def test_activate_without_required_fields_raises(db_session: AsyncSession):
    worker = await _create_minimal_worker(db_session)

    with pytest.raises(WorkerActivationIncompleteError):
        await worker_service.update_worker(
            db_session, worker.id, WorkerUpdateRequest(status=WorkerStatus.ACTIVE)
        )


async def test_activate_with_required_fields_succeeds(db_session: AsyncSession):
    worker = await _create_minimal_worker(db_session)

    activated = await worker_service.update_worker(
        db_session,
        worker.id,
        WorkerUpdateRequest(
            status=WorkerStatus.ACTIVE,
            phone="010-1234-5678",
            resident_registration_number="850315-1234567",
            bank_account_number="123-456-789",
        ),
    )

    assert activated.status == WorkerStatus.ACTIVE
    assert activated.resident_registration_number_masked == "850315-1******"


async def test_activate_reuses_previously_saved_sensitive_fields(db_session: AsyncSession):
    worker = await _create_minimal_worker(db_session)
    await worker_service.update_worker(
        db_session,
        worker.id,
        WorkerUpdateRequest(
            phone="010-1234-5678",
            resident_registration_number="850315-1234567",
            bank_account_number="123-456-789",
        ),
    )

    activated = await worker_service.update_worker(
        db_session, worker.id, WorkerUpdateRequest(status=WorkerStatus.ACTIVE)
    )

    assert activated.status == WorkerStatus.ACTIVE


async def test_changing_site_closes_previous_assignment_and_opens_new(
    db_session: AsyncSession, site_id, other_site_id
):
    worker = await worker_service.create_worker(
        db_session,
        WorkerCreateRequest(name="박민수", birth_date="1988-01-01", current_site_id=site_id),
    )

    await worker_service.update_worker(
        db_session, worker.id, WorkerUpdateRequest(current_site_id=other_site_id)
    )

    rows, _, _ = await site_assignment_repository.list_site_history(db_session, worker.id, None, 20)
    assert len(rows) == 2
    open_entries = [log for log, _ in rows if log.assigned_to is None]
    closed_entries = [log for log, _ in rows if log.assigned_to is not None]
    assert [log.site_id for log in open_entries] == [other_site_id]
    assert [log.site_id for log in closed_entries] == [site_id]


async def test_setting_same_site_again_does_not_duplicate_assignment(db_session: AsyncSession, site_id):
    worker = await worker_service.create_worker(
        db_session,
        WorkerCreateRequest(name="정수현", birth_date="1992-07-07", current_site_id=site_id),
    )

    await worker_service.update_worker(
        db_session, worker.id, WorkerUpdateRequest(current_site_id=site_id)
    )

    rows, _, _ = await site_assignment_repository.list_site_history(db_session, worker.id, None, 20)
    assert len(rows) == 1
