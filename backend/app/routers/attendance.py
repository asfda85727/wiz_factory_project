"""일일 출역 입력 라우터. site_id/date는 기획서 원문엔 없지만 현장별로 데이터가 분리되는
구조상 명시적 파라미터로 추가했다(사용자 확인 완료, 2026-07-20)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminContext, get_current_admin
from app.db.session import get_db_session
from app.schemas.attendance import (
    AttendanceDailyResponse,
    AttendanceDailySaveRequest,
    AttendanceListResponse,
    AttendanceRecordResponse,
    AttendanceUpdateRequest,
    WorkerMonthlyAttendanceResponse,
)
from app.services import attendance_service

router = APIRouter(prefix="/attendance", tags=["Attendance"], dependencies=[Depends(get_current_admin)])


@router.get("/daily", response_model=AttendanceDailyResponse)
async def get_daily_attendance(
    work_date: date = Query(alias="date"),
    site_id: UUID = Query(),
    trade: str | None = None,
    db: AsyncSession = Depends(get_db_session),
) -> AttendanceDailyResponse:
    return await attendance_service.get_daily(db, site_id, work_date, trade)


@router.post("/daily", response_model=AttendanceDailyResponse, status_code=201)
async def save_daily_attendance(
    payload: AttendanceDailySaveRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminContext = Depends(get_current_admin),
) -> AttendanceDailyResponse:
    response = await attendance_service.save_daily(db, UUID(admin.user_id), payload)
    await db.commit()
    return response


@router.post("/copy-previous", response_model=AttendanceDailyResponse, status_code=201)
async def copy_previous_attendance(
    work_date: date = Query(alias="date"),
    site_id: UUID = Query(),
    db: AsyncSession = Depends(get_db_session),
    admin: AdminContext = Depends(get_current_admin),
) -> AttendanceDailyResponse:
    response = await attendance_service.copy_previous(db, UUID(admin.user_id), site_id, work_date)
    await db.commit()
    return response


@router.patch("/{attendance_id}", response_model=AttendanceRecordResponse)
async def update_attendance_record(
    attendance_id: UUID,
    payload: AttendanceUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: AdminContext = Depends(get_current_admin),
) -> AttendanceRecordResponse:
    response = await attendance_service.update_attendance(db, UUID(admin.user_id), attendance_id, payload)
    await db.commit()
    return response


@router.get("/monthly", response_model=AttendanceListResponse)
async def get_monthly_attendance(
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
    site_id: UUID = Query(),
    db: AsyncSession = Depends(get_db_session),
) -> AttendanceListResponse:
    year_str, month_str = month.split("-")
    return await attendance_service.get_monthly(db, site_id, int(year_str), int(month_str))


@router.get("/worker-monthly", response_model=WorkerMonthlyAttendanceResponse)
async def get_worker_monthly_attendance(
    worker_id: UUID = Query(),
    month: str = Query(pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_session),
) -> WorkerMonthlyAttendanceResponse:
    year_str, month_str = month.split("-")
    return await attendance_service.get_worker_monthly(db, worker_id, int(year_str), int(month_str))
