# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

건설 일용직 노무비(임금) 관리 시스템. 두 개의 독립 앱으로 구성되며 공통 툴링(모노레포 빌드 등)은 없다:

- `backend/` — FastAPI + SQLAlchemy(async) + PostgreSQL + MinIO
- `frontend/` — React + Vite + TypeScript SPA

기획서(스코프, 데이터 모델, 개발 순서)는 저장소 밖 `새 폴더/기획서/` 경로에 있다. 진행 상황·의사결정 이력은 저장소 루트 `HANDOFF.md`에 계속 갱신되므로, 세션을 시작할 때 먼저 그 파일을 읽을 것.

- 코드 고칠 때마다 리로드를 믿지 말고 재시작 여부를 curl로 직접 재확인할것

## Commands

### Backend (`backend/`)

```bash
# 최초 1회
./.venv/Scripts/python.exe -m pip install -e .[dev]

# 로컬 인프라 (프로젝트 경로에 한글이 포함되어 -p 필수 — 안 하면 "project name must not be empty" 에러)
docker compose -p labor-cost up -d postgres minio

# 서버 실행 (포트 8000)
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload

# 테스트 (로컬 Postgres 컨테이너가 떠 있어야 함 — mock 없이 실제 DB로 검증)
./.venv/Scripts/python.exe -m pytest tests/ -v
./.venv/Scripts/python.exe -m pytest tests/test_worker_service.py::test_create_worker_minimal_registers_as_provisional -v

# 마이그레이션
./.venv/Scripts/python.exe -m alembic revision --autogenerate -m "설명"
./.venv/Scripts/python.exe -m alembic upgrade head

# 관리자 계정 시딩 (이메일 화이트리스트 등록)
./.venv/Scripts/python.exe scripts/seed_admin.py <email> <name>
```

### Frontend (`frontend/`)

```bash
npm run dev      # http://localhost:5173
npm run build    # tsc -b && vite build
npm run lint      # oxlint
```

### Windows 관련 주의사항

- Git Bash 콘솔이 명령줄 인자를 UTF-8이 아닌 로컬 코드페이지로 넘겨서, 한글이 포함된 `curl -d '{"name":"김철수"}'` 같은 인라인 요청은 깨진다. 우회: UTF-8로 파일에 먼저 쓰고 `curl --data-binary @file.json`(POST body), `curl --data-urlencode "search@<path>.txt"`(GET 쿼리) 사용. 파일 경로는 POSIX(`/c/...`)가 아니라 `cygpath -w`로 변환한 윈도우 경로여야 curl이 인식한다(multipart `-F "file=@..."`도 동일).
- asyncpg가 비ASCII(한글) 홈 디렉터리 경로에서 기본 sslmode 탐색 중 `OSError: Illegal byte sequence`를 던진다 — `app/db/session.py`와 `alembic/env.py` 양쪽 모두 `connect_args={"ssl": False}`로 우회 중(사내망 전용 DB라 SSL 불필요).
- pytest-asyncio가 테스트마다 새 이벤트 루프를 만드는데 asyncpg 커넥션은 자신을 만든 루프에 묶여 있어, 폴링된 커넥션을 다음 테스트(다른 루프)에서 재사용하면 `RuntimeError: Event loop is closed`가 난다 — `tests/conftest.py`의 autouse `_dispose_engine_after_test` 픽스처(매 테스트 후 `engine.dispose()`)로 해결되어 있다. 새 테스트 파일에서도 이 conftest를 그대로 상속하면 됨(별도 조치 불필요).

## Architecture

### 백엔드 계층 구조

`routers/` → `services/` → `repositories/` → `models/`. 라우터는 얇게 유지되며 인증은 `Depends(get_current_admin)`으로 라우터 레벨에서 강제된다(각 라우터 파일의 `APIRouter(..., dependencies=[...])`). 비즈니스 로직·검증은 전부 서비스 레이어에 있고, 리포지토리는 순수 쿼리만 담당한다(비즈니스 규칙 없음).

도메인별 예외는 `app/core/exceptions.py`의 `DomainError`를 상속하며, 전역 핸들러가 자동으로 RFC 7807 Problem Details JSON으로 변환한다(`type`/`title`/`status`/`detail`/`instance`) — 라우터·서비스에서 try/except로 HTTP 응답을 직접 만들 필요가 없다. 새 도메인 에러 추가 시 이 파일에 `status_code`/`problem_type`/`title`을 가진 서브클래스만 추가하면 됨.

### 인증 흐름

관리자 로그인은 아이디/비밀번호가 아니라 **구글/MS OAuth ID 토큰 검증 + 이메일 화이트리스트**다:

1. 프론트가 구글(`@react-oauth/google`)/MS(`@azure/msal-browser`, msal-react는 미사용) SDK로 로그인해 ID 토큰을 받음.
2. `POST /api/admin/login/{google,microsoft}`가 그 ID 토큰을 받아 `app/core/oauth.py`에서 JWKS 공개키로 서명·issuer·audience 검증(서버에 client secret 불필요 — 순수 OIDC 검증).
3. 검증된 이메일을 `users` 테이블(화이트리스트, 사전 등록 필요)과 대조(`app/services/auth_service.py`) — 없으면 401.
4. 통과하면 자체 세션 JWT 발급(`app/core/auth.py`, HS256) → 이후 모든 API 호출은 이 JWT를 `Authorization: Bearer`로 사용.

근로자 셀프 로그인(전화번호+주민번호+OTP)은 기획에는 있으나 아직 미구현.

### PII(주민등록번호·계좌번호) 처리

암호문(AES-256-GCM, `app/core/security.py`)과 마스킹 문자열을 **별도 컬럼**에 저장한다. 마스킹은 쓰기 시점에 한 번만 계산되고, 조회 경로는 절대 복호화하지 않는다(응답에는 `*_masked` 필드만 노출, 평문/암호문 필드는 어떤 응답 모델에도 없음). `ENCRYPTION_KEY_BASE64`는 정확히 32바이트로 디코딩되어야 하며 앱 기동 시(`app/config.py`) 검증 실패하면 즉시 죽는다.

### 노무비(payroll) 계산 엔진

`app/services/payroll_calculator.py`는 **순수 함수**(DB/외부 의존성 없음)로 소득세/지방소득세/고용보험/국민연금/건강보험/장기요양보험을 계산한다. 세율·연령 기준·최소 근무일수 등은 기획서 6.2절 값을 그대로 하드코딩한 것이며, 실제 LH 샘플 엑셀의 내장 수식 요율과 다른 부분이 있다는 걸 알고도 기획서 값을 채택하기로 한 결정임(파일 docstring 참고 — 요율을 "고치는" PR은 반드시 먼저 확인할 것).

계산 아키텍처는 애초에 LibreOffice headless 재계산 방식을 시도했다가 폐기하고 지금 방식(웹 화면은 시스템이 직접 계산, 제출용 엑셀은 값만 채워 넣고 엑셀 자체 수식이 파일을 열 때 재계산)으로 전환된 것 — `archive/구형_LibreOffice검증_20260714/`에 폐기된 접근이 보관되어 있다.

`payroll_service.recalculate_month()`는 출역(`is_present=true`) 있는 근로자만 대상으로 재계산하며 결과를 `payroll_results`에 upsert(재실행해도 안전, 멱등). `calc_status='held'`는 두 경우(임시등록 상태 / 대상월 단가 없음)에 안전하게 보류하는 용도 — 잘못된 금액을 내는 것보다 우선.

### 데이터 모델의 핵심 불변식

- `workers.current_site_id`: 근로자는 한 시점에 정확히 1개 현장만 소속. 변경 시 `site_assignment_log`에 이전 배정을 마감(오늘 날짜)하고 새 배정을 오픈하는 로직이 `worker_service.update_worker()`에 있다(발효일을 별도로 입력하는 API는 없음 — PATCH 시점=오늘 자동 기록).
- `worker_rates` / `attendance_records`: 근로자당 단가 1개, 하루 1현장(`UNIQUE(worker_id, work_date)`)을 강제한다. 다른 현장에 이미 등록된 근로자를 오늘 이 현장 명단에 추가하려 하면 조용히 덮어쓰지 않고 `AttendanceSiteConflictError`(409)로 막는다.
- 모든 테이블 PK는 Python `uuid4` 기본값의 UUID(BIGSERIAL 아님) — 개인정보를 다루는 소규모 내부 툴이라 ID enumeration 방지를 단순하게 우선한 선택.
- 목록 API는 전부 키셋 커서 페이지네이션(`app/core/pagination.py`, `CursorPage` 스키마) — offset 방식 아님.

### 프런트엔드

`src/services/apiClient.ts`가 유일한 API 진입점(컴포넌트에서 직접 `fetch` 금지) — JWT 자동 첨부, RFC7807 에러 응답을 `ApiError`로 변환, `FormData`는 자동으로 `Content-Type` 분기. `AuthContext` + `ProtectedRoute`가 토큰을 `localStorage`에 두고 미인증 시 `/login`으로 리다이렉트한다.

화면은 `src/pages/`에 라우트 단위로 존재(`LoginPage`/`WorkersPage`/`AttendancePage`/`PayrollPage`), 재사용 폼/패널은 `src/components/`(예: `WorkerDetailPanel`).

### OpenAPI 계약

`backend/openapi/workers.yaml`은 근로자/단가/현장 API의 설계 계약(Redocly lint + Prism mock으로 검증됨) — 실제 라우터 구현이 이 계약을 따라야 하며, 엔드포인트를 바꿀 때는 계약도 같이 갱신할 것.
