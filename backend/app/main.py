"""FastAPI 앱 진입점. CORS는 명시적 origin만 허용, 필수 설정은 app.config 임포트 시점에 검증된다."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.exceptions import DomainError, domain_error_handler, validation_error_handler
from app.routers import attendance, auth, health, payroll, rates, sites, workers
from app.services.file_storage import ensure_bucket


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket()
    yield


app = FastAPI(title="노무비 관리 시스템 API", version="1.0.0", lifespan=lifespan)

# 인증은 localStorage JWT를 Authorization: Bearer로 전송 — 쿠키를 쓰지 않으므로
# allow_credentials는 불필요하다(끄면 origin 설정 실수 시 노출 표면도 줄어든다).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_allowed_origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(workers.router, prefix="/api")
app.include_router(rates.router, prefix="/api")
app.include_router(sites.router, prefix="/api")
app.include_router(attendance.router, prefix="/api")
app.include_router(payroll.router, prefix="/api")
