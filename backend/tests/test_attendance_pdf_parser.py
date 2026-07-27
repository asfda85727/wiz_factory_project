from datetime import date
from pathlib import Path

from app.services.attendance_pdf_parser import parse_attendance_pdf

SAMPLE_PDF = Path(__file__).parent / "fixtures" / "tbm_예시.pdf"


def _load_sample() -> bytes:
    return SAMPLE_PDF.read_bytes()


def test_extracts_both_dates_from_real_sample():
    """tests/fixtures/tbm_예시.pdf 실측 대조: 2025-09-10/11 두 페이지."""
    result = parse_attendance_pdf(_load_sample())

    dates = {entry.work_date for entry in result.entries}
    assert dates == {date(2025, 9, 10), date(2025, 9, 11)}
    assert result.skipped_pages[0].page_number == 3
    assert "날짜를 인식하지 못함" in result.skipped_pages[0].reason


def test_duplicate_header_columns_kept_separate_not_merged():
    """같은 헤더("관리자"/"목수"/"철거")가 두 번 나오는 열도 그대로 별개 항목으로 추출."""
    result = parse_attendance_pdf(_load_sample())
    day1 = [e for e in result.entries if e.work_date == date(2025, 9, 10)]

    names_by_trade: dict[str, set[str]] = {}
    for entry in day1:
        names_by_trade.setdefault(entry.trade, set()).add(entry.name)

    assert "박상용" in names_by_trade["관리자"]
    assert "전종태" in names_by_trade["관리자"]
    assert "손한식" in names_by_trade["목수"]
    assert "노제우" in names_by_trade["철거"]
    assert "김희석" in names_by_trade["철거"]


def test_duplicate_header_columns_distinguished_by_column_index():
    """같은 "관리자" 헤더라도 물리적으로 다른 열(본대/철거팀)이면 column_index로 구분돼야
    화면에서 두 열이 섞이지 않고 원본 표 순서대로(세로로 먼저) 보여줄 수 있다."""
    result = parse_attendance_pdf(_load_sample())
    day1 = [e for e in result.entries if e.work_date == date(2025, 9, 10) and e.trade == "관리자"]

    by_column: dict[int, set[str]] = {}
    for entry in day1:
        by_column.setdefault(entry.column_index, set()).add(entry.name)

    assert len(by_column) == 2
    first_column_names = frozenset({"박상용", "정상문", "용역", "심효성", "강명연"})
    second_column_names = frozenset({"전종태", "장수현", "조윤섭", "박제호", "남동현"})
    assert {frozenset(names) for names in by_column.values()} == {first_column_names, second_column_names}


def test_order_column_excluded_as_trade():
    result = parse_attendance_pdf(_load_sample())
    assert all(entry.trade != "순서" for entry in result.entries)


def test_blank_cells_produce_no_entries():
    result = parse_attendance_pdf(_load_sample())
    day1_count = len([e for e in result.entries if e.work_date == date(2025, 9, 10)])
    # 실측: 관리자5+목수8+타일5+설비6+방화문2+철거5 + 철거(2열)1+관리자(2열)5+목수(2열)0 = 37
    assert day1_count == 37
