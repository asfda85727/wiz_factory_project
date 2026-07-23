"""월별 정산 파이프라인: 출역일수 + 단가 + payroll_calculator를 엮어 payroll_results를 채운다.

calc_status='held'로 보류하는 두 경우(기획서 6.4/10번 취지를 그대로 따름):
- 근로자가 아직 임시 등록(provisional) 상태인 경우
- 대상월에 적용할 단가(worker_rates)가 없는 경우 (근로자당 월 1개 단가를 가정 — 사용자 확인,
  월 중간 단가 변경은 실무상 없음)
둘 다 잘못된 금액을 계산해 내는 것보다 안전하게 보류하는 쪽을 택한다.
"""

import calendar
from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.payroll_result import PayrollResult
from app.repositories import payroll_repository, worker_repository
from app.schemas.payroll import PayrollListResponse, PayrollResultResponse
from app.schemas.worker import WorkerStatus
from app.services.payroll_calculator import calculate_payroll


def _month_bounds(year: int, month: int) -> tuple[date, date]:
    month_start = date(year, month, 1)
    month_end = date(year, month, calendar.monthrange(year, month)[1])
    return month_start, month_end


def _to_response(result: PayrollResult, worker_name: str, trade: str | None) -> PayrollResultResponse:
    return PayrollResultResponse(
        id=result.id,
        worker_id=result.worker_id,
        worker_name=worker_name,
        trade=trade,
        target_month=result.target_month,
        work_days=result.work_days,
        gross_pay=result.gross_pay,
        income_tax=result.income_tax,
        local_tax=result.local_tax,
        employment_insurance=result.employment_insurance,
        national_pension=result.national_pension,
        health_insurance=result.health_insurance,
        long_term_care=result.long_term_care,
        net_pay=result.net_pay,
        calc_status=result.calc_status,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


async def _upsert_result(
    db: AsyncSession,
    worker_id,
    target_month: date,
    work_days: int,
    calc_status: str,
    payroll_values: dict[str, int] | None = None,
) -> PayrollResult:
    existing = await payroll_repository.get_by_worker_and_month(db, worker_id, target_month)
    values = payroll_values or {
        "gross_pay": 0,
        "income_tax": 0,
        "local_tax": 0,
        "employment_insurance": 0,
        "national_pension": 0,
        "health_insurance": 0,
        "long_term_care": 0,
        "net_pay": 0,
    }

    if existing is not None:
        existing.work_days = work_days
        existing.calc_status = calc_status
        for key, value in values.items():
            setattr(existing, key, value)
        return existing

    result = PayrollResult(
        worker_id=worker_id, target_month=target_month, work_days=work_days, calc_status=calc_status, **values
    )
    db.add(result)
    return result


async def recalculate_month(db: AsyncSession, year: int, month: int) -> PayrollListResponse:
    month_start, month_end = _month_bounds(year, month)
    worker_ids = await payroll_repository.list_present_worker_ids_for_month(db, month_start, month_end)

    # 더 이상 그 달에 출역이 없는 근로자의 잔존 결과를 먼저 정리(유령 명세서 방지)
    await payroll_repository.delete_results_except(db, month_start, worker_ids)

    results = []
    info: dict[UUID, tuple[str, str | None]] = {}
    for worker_id in worker_ids:
        worker = await worker_repository.get_worker_by_id(db, worker_id)
        info[worker_id] = (worker.name, worker.trade)
        work_days = await payroll_repository.count_present_days(db, worker_id, month_start, month_end)

        if worker.status == WorkerStatus.PROVISIONAL.value:
            results.append(await _upsert_result(db, worker_id, month_start, work_days, "held"))
            continue

        rate = await payroll_repository.find_rate_for_month(db, worker_id, month_start, month_end)
        if rate is None:
            results.append(await _upsert_result(db, worker_id, month_start, work_days, "held"))
            continue

        calculated = calculate_payroll(
            daily_rate=rate.daily_rate, attendance_days=work_days, birth_date=worker.birth_date, month_end=month_end
        )
        results.append(
            await _upsert_result(
                db,
                worker_id,
                month_start,
                work_days,
                "ok",
                {
                    "gross_pay": calculated.gross_pay,
                    "income_tax": calculated.income_tax,
                    "local_tax": calculated.local_tax,
                    "employment_insurance": calculated.employment_insurance,
                    "national_pension": calculated.national_pension,
                    "health_insurance": calculated.health_insurance,
                    "long_term_care": calculated.long_term_care,
                    "net_pay": calculated.net_pay,
                },
            )
        )

    await db.flush()
    for result in results:
        await db.refresh(result)
    return PayrollListResponse(
        data=[_to_response(r, *info.get(r.worker_id, ("", None))) for r in results]
    )


async def get_month(db: AsyncSession, year: int, month: int) -> PayrollListResponse:
    month_start, _ = _month_bounds(year, month)
    results = await payroll_repository.list_by_month(db, month_start)
    info = await worker_repository.get_name_trade_by_ids(db, [r.worker_id for r in results])
    return PayrollListResponse(
        data=[_to_response(r, *info.get(r.worker_id, ("", None))) for r in results]
    )
