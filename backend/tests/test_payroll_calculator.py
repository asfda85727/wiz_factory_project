from datetime import date

from app.services.payroll_calculator import calculate_payroll

MONTH_END = date(2025, 6, 30)


def test_matches_real_lh_sample_worker():
    """samples/노무비 예시.xlsx 워커1(row6-7) 실측 캐시값과 대조: 소득세1350/지방세130/고용보험1800, 60세 이상·8일 미만이라 연금·건보·장기요양은 0."""
    result = calculate_payroll(
        daily_rate=200_000,
        attendance_days=1,
        birth_date=date(1960, 10, 21),
        month_end=MONTH_END,
    )

    assert result.gross_pay == 200_000
    assert result.income_tax == 1_350
    assert result.local_tax == 130
    assert result.employment_insurance == 1_800
    assert result.national_pension == 0
    assert result.health_insurance == 0
    assert result.long_term_care == 0
    assert result.net_pay == 196_720


def test_income_tax_below_minimum_collectible_is_not_charged():
    result = calculate_payroll(
        daily_rate=160_000,
        attendance_days=1,
        birth_date=date(1990, 1, 1),
        month_end=MONTH_END,
    )

    assert result.income_tax == 0
    assert result.local_tax == 0


def test_daily_rate_below_deduction_threshold_has_no_taxable_base():
    result = calculate_payroll(
        daily_rate=140_000,
        attendance_days=10,
        birth_date=date(1990, 1, 1),
        month_end=MONTH_END,
    )

    assert result.income_tax == 0
    assert result.local_tax == 0


def test_national_pension_applies_under_60_with_8_or_more_days():
    result = calculate_payroll(
        daily_rate=200_000,
        attendance_days=10,
        birth_date=date(1990, 1, 1),
        month_end=MONTH_END,
    )

    assert result.gross_pay == 2_000_000
    assert result.income_tax == 13_500
    assert result.local_tax == 1_350
    assert result.employment_insurance == 18_000
    assert result.national_pension == 95_000
    assert result.health_insurance == 71_900
    assert result.long_term_care == 9_440
    assert result.net_pay == 1_790_810


def test_national_pension_applies_via_income_threshold_despite_under_8_days():
    result = calculate_payroll(
        daily_rate=500_000,
        attendance_days=5,
        birth_date=date(1995, 5, 5),
        month_end=MONTH_END,
    )

    assert result.gross_pay == 2_500_000
    assert result.national_pension == 118_750
    assert result.health_insurance == 0
    assert result.long_term_care == 0


def test_national_pension_not_applied_at_age_60():
    result = calculate_payroll(
        daily_rate=200_000,
        attendance_days=10,
        birth_date=date(1965, 6, 30),
        month_end=MONTH_END,
    )

    assert result.national_pension == 0


def test_employment_insurance_not_applied_under_20():
    result = calculate_payroll(
        daily_rate=200_000,
        attendance_days=10,
        birth_date=date(2006, 7, 1),
        month_end=MONTH_END,
    )

    assert result.employment_insurance == 0


def test_employment_insurance_not_applied_at_65_or_older():
    result = calculate_payroll(
        daily_rate=200_000,
        attendance_days=10,
        birth_date=date(1960, 6, 30),
        month_end=MONTH_END,
    )

    assert result.employment_insurance == 0
