"""한글에서 내보낸 일일 출역 PDF 파싱 (기획서 12번 8번).

표 구조는 파일마다 같지만 공정 열의 개수·순서는 달라질 수 있어 열 위치가
아니라 헤더 텍스트로 공정을 인식한다. 헤더 행 앞에 현장명 등이 적힌 제목
행이 올 수 있어(`tests/fixtures/tbm_예시.pdf` 실측 확인), "순서" 셀이 있는
첫 행을 헤더로 판단한다.
"""

import io
from dataclasses import dataclass, field
from datetime import date

import pdfplumber

ORDER_COLUMN_HEADER = "순서"
DATE_PATTERN = r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일"


# column_index: 원본 표에서의 열 위치. 같은 공정명 열이 두 번 나와도(예: 관리자 열이
# 본대/철거팀 각각 따로 있는 경우) 물리적으로 다른 열이므로 화면에 보여줄 때 섞이지 않게 구분한다.
@dataclass(frozen=True)
class ParsedEntry:
    work_date: date
    trade: str
    name: str
    column_index: int


@dataclass(frozen=True)
class SkippedPage:
    page_number: int
    reason: str


@dataclass(frozen=True)
class ParsedPdfResult:
    entries: list[ParsedEntry] = field(default_factory=list)
    skipped_pages: list[SkippedPage] = field(default_factory=list)


def _clean(cell: str | None) -> str:
    if cell is None:
        return ""
    return " ".join(cell.split())


def _extract_work_date(page_text: str | None) -> date | None:
    if not page_text:
        return None
    import re

    match = re.search(DATE_PATTERN, page_text)
    if match is None:
        return None
    year, month, day = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _find_header_row_index(table: list[list[str | None]]) -> int | None:
    for index, row in enumerate(table):
        if any(_clean(cell) == ORDER_COLUMN_HEADER for cell in row):
            return index
    return None


def _trade_columns(header_row: list[str | None]) -> dict[int, str]:
    columns: dict[int, str] = {}
    for index, cell in enumerate(header_row):
        header_text = _clean(cell)
        if not header_text or header_text == ORDER_COLUMN_HEADER:
            continue
        columns[index] = header_text
    return columns


def _parse_page(page_number: int, page: "pdfplumber.page.Page") -> tuple[list[ParsedEntry], SkippedPage | None]:
    work_date = _extract_work_date(page.extract_text())
    if work_date is None:
        return [], SkippedPage(page_number, "날짜를 인식하지 못함")

    table = page.extract_table()
    if not table:
        return [], SkippedPage(page_number, "표를 인식하지 못함")

    header_index = _find_header_row_index(table)
    if header_index is None:
        return [], SkippedPage(page_number, "'순서' 열을 찾지 못함")

    trade_columns = _trade_columns(table[header_index])
    if not trade_columns:
        return [], SkippedPage(page_number, "공정 열을 찾지 못함")

    entries: list[ParsedEntry] = []
    for row in table[header_index + 1 :]:
        for column_index, trade in trade_columns.items():
            if column_index >= len(row):
                continue
            cell = row[column_index]
            if cell is None:
                continue
            for line in cell.splitlines():
                name = _clean(line)
                if name:
                    entries.append(
                        ParsedEntry(work_date=work_date, trade=trade, name=name, column_index=column_index)
                    )
    return entries, None


def parse_attendance_pdf(pdf_bytes: bytes) -> ParsedPdfResult:
    entries: list[ParsedEntry] = []
    skipped_pages: list[SkippedPage] = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_entries, skipped = _parse_page(page_number, page)
            entries.extend(page_entries)
            if skipped is not None:
                skipped_pages.append(skipped)

    return ParsedPdfResult(entries=entries, skipped_pages=skipped_pages)
