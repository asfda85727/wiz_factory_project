"""기획서 6.2 노무비 계산 공식 구현.

요율 출처: 기획서(2026-07-16) 6.2. 국민연금(4.75%)은 기획서 6.4-1에서
실측 대조 생략을 명시적으로 결정. 건강보험(3.595%)·장기요양(13.14%)은
실제 LH 샘플 파일(2025-06 데이터)의 내장 수식이 각각 3.545%/12.95%를
쓰고 있어 차이가 있으나, 사용자 확인 결과 기획서 수치를 그대로 채택.
"""

import math
from dataclasses import dataclass
from datetime import date

DAILY_INCOME_DEDUCTION = 150_000
MINIMUM_COLLECTIBLE_INCOME_TAX = 1_000

INCOME_TAX_RATE = 0.06
INCOME_TAX_DEDUCTION_RATE = 0.45
LOCAL_TAX_RATE = 0.10
EMPLOYMENT_INSURANCE_RATE = 0.009
NATIONAL_PENSION_RATE = 0.0475
HEALTH_INSURANCE_RATE = 0.03595
LONG_TERM_CARE_RATE = 0.1314

EMPLOYMENT_INSURANCE_MIN_AGE = 20
EMPLOYMENT_INSURANCE_MAX_AGE = 65
NATIONAL_PENSION_AGE_LIMIT = 60
INSURANCE_MIN_WORK_DAYS = 8
NATIONAL_PENSION_INCOME_THRESHOLD = 2_200_000


@dataclass(frozen=True)
class PayrollResult:
    gross_pay: int
    income_tax: int
    local_tax: int
    employment_insurance: int
    national_pension: int
    health_insurance: int
    long_term_care: int
    net_pay: int


def round_down_to_ten(amount: float) -> int:
    return math.floor(round(amount, 6) / 10) * 10


def calculate_age(birth_date: date, as_of: date) -> int:
    age = as_of.year - birth_date.year
    if (as_of.month, as_of.day) < (birth_date.month, birth_date.day):
        age -= 1
    return age


def calculate_payroll(
    daily_rate: int,
    attendance_days: int,
    birth_date: date,
    month_end: date,
) -> PayrollResult:
    gross_pay = daily_rate * attendance_days
    age = calculate_age(birth_date, month_end)

    taxable_daily_excess = max(daily_rate - DAILY_INCOME_DEDUCTION, 0)
    taxable_base = taxable_daily_excess * attendance_days

    raw_income_tax = round_down_to_ten(
        taxable_base * INCOME_TAX_RATE * INCOME_TAX_DEDUCTION_RATE
    )
    income_tax = raw_income_tax if raw_income_tax >= MINIMUM_COLLECTIBLE_INCOME_TAX else 0
    local_tax = round_down_to_ten(income_tax * LOCAL_TAX_RATE)

    employment_insurance = 0
    if EMPLOYMENT_INSURANCE_MIN_AGE <= age < EMPLOYMENT_INSURANCE_MAX_AGE:
        employment_insurance = round_down_to_ten(gross_pay * EMPLOYMENT_INSURANCE_RATE)

    national_pension = 0
    if age < NATIONAL_PENSION_AGE_LIMIT and (
        attendance_days >= INSURANCE_MIN_WORK_DAYS
        or gross_pay >= NATIONAL_PENSION_INCOME_THRESHOLD
    ):
        national_pension = round_down_to_ten(gross_pay * NATIONAL_PENSION_RATE)

    health_insurance = 0
    if attendance_days >= INSURANCE_MIN_WORK_DAYS:
        health_insurance = round_down_to_ten(gross_pay * HEALTH_INSURANCE_RATE)

    long_term_care = round_down_to_ten(health_insurance * LONG_TERM_CARE_RATE)

    net_pay = (
        gross_pay
        - income_tax
        - local_tax
        - employment_insurance
        - national_pension
        - health_insurance
        - long_term_care
    )

    return PayrollResult(
        gross_pay=gross_pay,
        income_tax=income_tax,
        local_tax=local_tax,
        employment_insurance=employment_insurance,
        national_pension=national_pension,
        health_insurance=health_insurance,
        long_term_care=long_term_care,
        net_pay=net_pay,
    )
