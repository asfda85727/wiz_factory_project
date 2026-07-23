"""커서 페이지네이션 인코딩/디코딩 공통 유틸 (키셋 방식). 각 repository가 정렬 키에 맞게 사용한다."""

import base64


def encode_cursor(*parts: str) -> str:
    raw = "|".join(parts)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def decode_cursor(cursor: str) -> list[str]:
    raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
    return raw.split("|")
