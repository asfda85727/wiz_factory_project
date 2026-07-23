"""도메인 커스텀 예외 + RFC 7807 Problem Details 변환.

problem_type은 backend/openapi/workers.yaml 응답 설명에 대응한다(에러 카탈로그와 코드가 어긋나지 않도록).
"""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_BASE_URI = "https://laborcost.internal/problems"

_VALIDATION_ERROR_MESSAGES = {
    "missing": "필수 항목입니다",
    "string_type": "문자열이어야 합니다",
    "int_type": "숫자여야 합니다",
    "int_parsing": "숫자 형식이 아닙니다",
    "float_parsing": "숫자 형식이 아닙니다",
    "bool_parsing": "true/false 값이어야 합니다",
    "date_parsing": "날짜 형식이 올바르지 않습니다(YYYY-MM-DD)",
    "date_from_datetime_parsing": "날짜 형식이 올바르지 않습니다(YYYY-MM-DD)",
    "uuid_parsing": "형식이 올바르지 않습니다",
    "string_pattern_mismatch": "형식이 올바르지 않습니다",
    "greater_than_equal": "0 이상의 값이어야 합니다",
    "value_error": "값이 올바르지 않습니다",
}


class DomainError(Exception):
    status_code: int = 400
    problem_type: str = "domain-error"
    title: str = "Domain Error"

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class NotFoundError(DomainError):
    status_code = 404
    problem_type = "not-found"
    title = "Resource Not Found"


class RatePeriodOverlapError(DomainError):
    status_code = 409
    problem_type = "rate-period-overlap"
    title = "Rate Period Overlap"


class WorkerActivationIncompleteError(DomainError):
    status_code = 409
    problem_type = "worker-activation-incomplete"
    title = "Worker Activation Incomplete"


class AttendanceSiteConflictError(DomainError):
    status_code = 409
    problem_type = "attendance-site-conflict"
    title = "Attendance Site Conflict"


class UnsupportedFileTypeError(DomainError):
    status_code = 415
    problem_type = "unsupported-file-type"
    title = "Unsupported File Type"


class FileTooLargeError(DomainError):
    status_code = 413
    problem_type = "file-too-large"
    title = "File Too Large"


class UnauthorizedError(DomainError):
    status_code = 401
    problem_type = "unauthorized"
    title = "Unauthorized"


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        media_type="application/problem+json",
        content={
            "type": f"{PROBLEM_BASE_URI}/{exc.problem_type}",
            "title": exc.title,
            "status": exc.status_code,
            "detail": exc.detail,
            "instance": str(request.url.path),
        },
    )


def _validation_field_label(loc: tuple) -> str:
    parts = [str(part) for part in loc if part not in ("body", "query", "path")]
    return ".".join(parts) if parts else "요청"


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    messages = [
        f"{_validation_field_label(error.get('loc', ()))}: "
        f"{_VALIDATION_ERROR_MESSAGES.get(error.get('type', ''), '값이 올바르지 않습니다')}"
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        media_type="application/problem+json",
        content={
            "type": f"{PROBLEM_BASE_URI}/validation-error",
            "title": "Validation Error",
            "status": 422,
            "detail": " / ".join(messages) if messages else "요청 형식이 올바르지 않습니다.",
            "instance": str(request.url.path),
        },
    )
