"""월별 정산 결과 조회/재계산 라우터."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_admin
from app.db.session import get_db_session
from app.schemas.payroll import PayrollListResponse
from app.services import payroll_service

router = APIRouter(prefix="/payroll", tags=["Payroll"], dependencies=[Depends(get_current_admin)])


def _parse_month(month: str) -> tuple[int, int]:
    year_str, month_str = month.split("-")
    return int(year_str), int(month_str)


@router.get("", response_model=PayrollListResponse)
async def get_payroll(
    month: str = Query(pattern=r"^\d{4}-\d{2}$"), db: AsyncSession = Depends(get_db_session)
) -> PayrollListResponse:
    year, month_num = _parse_month(month)
    return await payroll_service.get_month(db, year, month_num)


@router.post("/recalculate", response_model=PayrollListResponse, status_code=201)
async def recalculate_payroll(
    month: str = Query(pattern=r"^\d{4}-\d{2}$"), db: AsyncSession = Depends(get_db_session)
) -> PayrollListResponse:
    year, month_num = _parse_month(month)
    response = await payroll_service.recalculate_month(db, year, month_num)
    await db.commit()
    return response
