# 노무비 관리 시스템 - 작업 진행 상황 정리

**작성 일자:** 2026-07-16 (2026-07-14 버전에서 갱신)
**프로젝트:** 노무비-관리-시스템 (FastAPI + React(Vite) + PostgreSQL)

---

## 1. 완료된 작업

### 1.1 기획서 확정 (2026-07-16 갱신판)
- ✅ 기획서 전면 구체화: `C:\Users\위즈팩토리\Desktop\새 폴더\기획서\노무비_관리_시스템_기획서.md`
  - MVP 범위 확정 (9개 기능), 제외 범위 명시
  - 데이터 모델 11개 테이블, REST API 엔드포인트 설계 완료
  - 개발 순서 10단계 확정 (12번)
  - 경쟁사 10곳 조사 + 차별점 정리 (8번)

### 1.2 핵심 아키텍처 전환 — LibreOffice 재계산 폐기
- ✅ **이중 계산 구조로 전환** (기획서 6.1)
  - 웹 명세서/셀프조회/대시보드 → 시스템이 표준 공식으로 직접 계산
  - 제출용 엑셀 → 값만 채우고, 엑셀 자체 내장 수식이 파일 열 때 계산 (LibreOffice 불필요)
- ✅ 세금 공식 명시적으로 확정 (기획서 6.2): 소득세/지방소득세/고용보험/국민연금/건강보험/장기요양보험 각 공식
- ✅ 2026-07-14 세션의 LibreOffice headless 재계산 검증 스크립트 8개는
  `archive/구형_LibreOffice검증_20260714/`로 보관 처리 (목적 소멸, 삭제는 안 함 — README 참고)

### 1.3 프로젝트 환경 구성 (2026-07-14, 유효)
- ✅ 프로젝트 폴더: `C:\Users\위즈팩토리\Desktop\노무비-관리-시스템\`
- ✅ 스킬 27개 설치 (`.claude/skills/`)
- ✅ Python 3.12.10, LibreOffice 설치 (LibreOffice는 더 이상 계산 경로에 필요 없음 — 설치만 유지)

### 1.4 기술 검증 — 파일 구조 (2026-07-14, 유효)
- ✅ 샘플 파일 `노무비 예시.xlsx` 분석: VBA 매크로 없음, 시트 2개(명세서_철거/증빙_철거), 병합 셀 251개
- ✅ LH 원본 양식 셀 위치 확인 (기획서 7번에 표로 반영됨: 이름 B열, 노무비단가 W열 등)

---

## 2. 의사결정 사항 (최신)

| 항목 | 결정 | 근거 |
|------|------|------|
| **계산 엔진** | ~~LibreOffice headless 재계산~~ → **시스템 직접 계산 + openpyxl 값 채움** | Y6/Y7 원본 수식 불일치로 막혔던 문제를 아키텍처 전환으로 우회 |
| **명단 입력** | 수기 입력 → **PDF 업로드 자동 추출**(pdfplumber/PyMuPDF) + 검수 화면 | 한글에서 내보낸 텍스트 기반 PDF, 반복 수기 입력 제거가 목적 |
| **현장 정의** | 현장 = 프로젝트/계약 단위 (지역 라벨 아님) | 발주처가 다른 여러 프로젝트를 오가는 실무 확인 |
| **다현장 여부** | 근로자는 한 시점에 정확히 1개 현장만 소속 | 단순화, `current_site_id` + 이동 이력으로 관리 |
| **근로자 로그인** | 전화번호+주민번호 앞자리 + **OTP 문자 인증** | 정보 앎이 아니라 휴대폰 소지 확인으로 보완 |
| **공정(trade) 데이터** | PDF 자동 추출로만 확보, 관리자 수동 입력 화면 없음 (검수 중 수정만 가능) | "반복 수기 입력 제거" 목적과 모순 방지 |
| **원청 양식 매핑** | 시작 셀 + 반복 간격 입력 방식 (자동 헤더 감지 미채택) | 개발량 대비 입력 편의성 균형 |
| **코드 언어** | 식별자는 영어, 주석/로그/문서는 한글 | [[feedback_code_language]] |
| **기술 스택** | FastAPI + React(Vite SPA) + PostgreSQL + Docker Compose | 1인 개발, 로그인 뒤 내부 도구라 SSR 이점 없음 |

---

## 3. 현재 상태 요약

### 기술 검증 진행률
```
[==============================        ] 85%
- 파일 구조 분석 ✅
- 계산 아키텍처 확정 ✅ (이중 계산 구조로 전환, LibreOffice 이슈 우회)
- 세금 공식 명시 ✅ (기획서 6.2)
- 계산 로직 Python 구현 + 실측 대조 ✅ (아래 4.1 참고)
- "나머지" 시트 분류 기준 🔜 (미확인)
```

### 4.1 계산 로직 검증 결과 (2026-07-16)
- ✅ `backend/app/services/payroll_calculator.py` 구현 완료
- ✅ pytest 8개 전부 통과 (`backend/tests/test_payroll_calculator.py`)
- ✅ **실측 대조 성공**: `samples/노무비 예시.xlsx`의 실제 캐시값(워커1, row6-7)과
  Python 계산 결과가 정확히 일치 — 소득세 1,350원 / 지방소득세 130원 / 고용보험 1,800원
  (이전 세션 Issue #1의 "Y6/Y7 세금 공식 불일치"는 수식 해석 오류였고, 실제로는
  기획서 6.2와 정확히 일치함이 확인됨)
- ⚠️ **요율 확인 사항**: 건강보험(3.595%)·장기요양보험(13.14%)은 기획서 값이 실제
  LH 샘플 파일(2025-06 데이터)의 내장 수식 요율(3.545%/12.95%)과 다름. 사용자가
  기획서 수치를 그대로 채택하기로 결정 — 코드에도 그렇게 반영됨. 국민연금(4.75%)도
  샘플 파일 실제 수식(4.5%)과 다르지만 기획서 6.4-1에서 이미 대조 생략으로 결정된 사항.
  → 이 세 요율이 실제 2026년 공식 요율과 맞는지는 별도 확인 안 함(사용자 지시로 스킵)

### 개발 준비 상태
```
기획서 확정             ✅
데이터 모델/API 설계    ✅ (기획서 10, 11번)
스택 설치               ✅ (Python, LibreOffice — 계산엔 불필요, 참고용 유지)
스킬 통합               ✅ (27개)
개발 순서 확정          ✅ (기획서 12번, 아래 5번 섹션에 반영)
데이터베이스 스키마      ✅ (6개 테이블, Alembic 적용 완료)
근로자 마스터 API       ✅ (2026-07-20 E2E 검증 + 테스트 26개 통과로 완료)
프런트엔드              🔜 (다음 단계, 아직 미착수)
```

---

## 4. 남은 이슈 (기획서 13번 기준)

| 항목 | 심각도 | 상태 |
|------|--------|------|
| 소액부징수(1,000원 미만 미징수)·절사 규칙 실측 대조 | HIGH | ✅ 완료 — payroll_calculator.py 구현 + 테스트 통과 (4.1 참고) |
| "나머지" 시트 분류 기준 (캐치올인지 별도 규칙인지) | MEDIUM | 미확인 — 실제 양식 파일로 확인 필요 |
| 문제 검증 (다른 하도급업체도 동일 문제 겪는지, 지불 의향) | HIGH (배포 전제) | 0건 진행 — `validate-idea` 권장 |
| 홈택스 일용근로소득 지급명세서 분기 신고 연계 가능성 | MEDIUM | Jun님께 실제 신고 여부 확인 요청 필요 (미발송) |
| 4대보험 EDI 파일신고 연계 | LOW | 오픈API 없음 확인, 검토만 된 상태 |
| 주민등록번호 수집 법적 근거 | HIGH (운영 전환 전 필수) | 현장 동의서 확보 중, 법무 검토 전 |
| 화면 와이어프레임 | - | 다음 단계 (일일 입력 화면부터) |

> 이전 세션의 "Issue #1: 세금 계산 공식 정확성(HIGH)"은 아키텍처 전환으로 검증 방식이
> 바뀌었을 뿐 완전히 사라진 건 아님 — 위 표 1번(소액부징수·절사 규칙 실측 대조)으로 이어짐.

---

## 5. 다음 단계 — 기획서 12번 개발 순서

```
1. 계산 로직 + 검증 테스트   ✅ 완료 (2026-07-16)
2. 근로자 마스터 (임시 등록 + 전체 검색 + 현장 소속 필드)   ✅ 완료 (2026-07-20)
3. 일일 출역 입력 (수동 — 자동완성/전일 복사)   ✅ 완료 (2026-07-20) — 아래 3번 섹션 참고
4. payroll_results 계산 파이프라인   ✅ 완료 (2026-07-20) — 아래 4번 섹션 참고
5. 웹 명세서 화면   ✅ 완료 (2026-07-20, 프런트엔드 스캐폴딩과 함께) — 아래 "프런트엔드" 섹션 참고
6. 양식 업로드 + 셀 매핑 화면 (LH 양식으로 첫 구현·검증)
7. 제출용 엑셀 생성
8. 명단 PDF 자동 기입 (pdfplumber/PyMuPDF + 검수 모드)
9. 대시보드 + 서류 미비 추적
10. 근로자 셀프 조회
```

**2번(근로자 마스터) — 2026-07-20 세션에서 완료:**
- [x] API 계약 설계 완료 — `backend/openapi/workers.yaml` (근로자/단가/현장, OpenAPI 3.1, Redocly lint 0 errors, Prism mock 검증 완료).
- [x] FastAPI 프로젝트 뼈대 구성 완료 (`backend/app/main.py`, `config.py`, `db/`, `core/`, `models/`, `schemas/`, `repositories/`, `services/`, `routers/`)
- [x] PostgreSQL 연결 + `users`, `sites`, `workers`, `worker_rates`, `site_assignment_log`, `rate_audit_log` 테이블 Alembic 마이그레이션 생성·적용 완료(`docker exec ... psql \dt`로 6개 테이블 확인)
- [x] `POST/GET /api/workers`, `GET /api/workers/{id}`, `PATCH /api/workers/{id}`, 단가(`/rates`), 현장(`/sites`), 현장이동이력(`/site-history`) 구현 완료
- [x] 관리자 로그인(`POST /api/admin/login`, JWT) — 근로자 셀프 로그인(OTP)은 별도 기능, 미구현
- [x] 신분증/통장 파일 업로드 라우트(`POST/GET /workers/{id}/files`) 구현 완료 — MinIO 연동
- [x] **curl E2E 검증 완료(2026-07-20)** — Git Bash 한글 인코딩 문제의 실제 원인 확정: 콘솔이 인자를 UTF-8이 아닌 로컬 코드페이지로 curl에 넘겨서 발생. 우회법: POST body는 `--data-binary @file.json`(UTF-8로 파일에 먼저 씀), GET 쿼리 파라미터는 `--data-urlencode "search@<윈도우경로>.txt"`(POSIX 경로 `/c/...`가 아니라 `cygpath -w`로 변환한 윈도우 경로 필요 — 안 그러면 curl이 "Failed to open/read local data from file" 에러). multipart 업로드(`-F "file=@..."`)도 동일하게 윈도우 경로 필요.
  근로자 등록(한글 이름)/현장 생성(한글 주소)/검색(`search=`)/단가 겹침(409)/정식전환 실패(409)·성공(200)/파일 업로드·다운로드(바이너리 일치) 전부 재검증 완료.
- [x] **버그 수정: MinIO 버킷 미생성** — `file_storage.py`의 `ensure_bucket()`이 정의만 되어 있고 어디서도 호출되지 않아 파일 업로드가 500(`NoSuchBucket`)으로 실패했음. `main.py`에 FastAPI `lifespan`으로 앱 시작 시 호출하도록 연결.
- [x] **기능 공백 발견 및 구현: 현장이동이력 쓰기 누락** — `GET /workers/{id}/site-history` 조회는 있었지만 `site_assignment_log`에 기록하는 코드가 전혀 없어 항상 빈 배열만 반환했음(설계 시 읽기 쪽만 만들고 쓰기 쪽을 빠뜨림). 사용자 결정: **PATCH 시점=오늘 자동 기록** 방식 채택(별도 발효일 입력 API는 만들지 않음). `worker_service.create_worker`(최초 배정 시 오픈 항목 생성)와 `update_worker`(current_site_id 변경 시 기존 오픈 항목을 오늘 날짜로 마감 + 새 오픈 항목 생성)에 구현, `site_assignment_repository`에 `close_open_assignment`/`create_assignment` 추가.
- [x] **신규 유닛/통합 테스트 18개 추가** (`backend/tests/test_auth.py` 6개, `test_rate_service.py` 4개, `test_worker_service.py` 8개) — 전체 26개 통과. auth는 순수함수 단위테스트, worker/rate service는 로컬 Postgres에 붙되 트랜잭션 롤백으로 격리(`tests/conftest.py`). **Windows 특이사항**: pytest-asyncio가 테스트마다 새 이벤트루프를 만드는데 asyncpg 커넥션은 만들어진 이벤트루프에 묶여있어 폴링된 커넥션 재사용 시 `RuntimeError: Event loop is closed`가 남 — `conftest.py`에 테스트마다 `engine.dispose()`하는 autouse 픽스처로 해결.
- [x] `backend/.env`의 JWT_SECRET/ENCRYPTION_KEY_BASE64/MinIO 자격증명은 로컬 개발용으로 무작위 생성된 값 — 운영 배포 전 반드시 재발급(계속 유효한 남은 작업).
- 로컬 admin 계정 비밀번호를 2026-07-20 세션에서 `devpass123`으로 재설정함(이전 비밀번호를 몰라 로그인 테스트가 막혀 있었음) — 로컬 개발 DB에서만 유효, 운영 배포 시 무관.

**3번(일일 출역 입력) — 2026-07-20 세션에서 완료:**
- 착수 전 기획서 12번 개발순서 원문을 다시 대조 확인함(사용자 요청) — HANDOFF.md에 적혀있던 순서와 실제로 일치, 어긋난 부분 없음.
- [x] 데이터 모델(기획서 10장 그대로): `attendance_records`(worker_id, site_id, work_date, trade, is_present, recorded_by/at, updated_at, `UNIQUE(worker_id, work_date)`로 하루 1현장 강제) + `attendance_audit_log`. Alembic 마이그레이션 적용 완료.
- [x] **기획서 원문에 없어서 사용자에게 확인받은 설계 결정 2건**: ① `GET /attendance/monthly`, `POST /attendance/copy-previous`는 기획서엔 `month=`/`date=`만 있었지만 현장별로 데이터가 나뉘므로 `site_id` 쿼리 파라미터를 추가함(사용자 확인). ② monthly 응답은 "근로자×날짜 그리드"가 아니라 단순 레코드 리스트로 최소하게 설계(5번 웹 명세서 화면이 아직 미확정이라 그리드 모양을 지금 정하는 건 과설계로 판단, 사용자 확인).
- [x] API 구현 완료: `GET/POST /api/attendance/daily`(일괄저장, 인원 합계 포함), `POST /api/attendance/copy-previous`(전일 복사), `PATCH /api/attendance/{id}`(개별수정 + audit log), `GET /api/attendance/monthly`.
- [x] **현장 충돌 방지**: 근로자가 이미 다른 현장에 같은 날짜로 등록돼 있으면(하루 1현장 원칙) 조용히 덮어쓰지 않고 `AttendanceSiteConflictError`(409)로 막음 — 일괄저장/전일복사 둘 다 적용.
- [x] pytest 11개 추가(`test_attendance_service.py`) — 전체 37개 통과.
- [x] curl E2E 검증 완료 — 일괄저장(한글 공정명 "철거")/조회/전일복사/개별수정/월간조회/현장충돌(409) 전부 확인.
**4번(payroll_results 계산 파이프라인) — 2026-07-20 세션에서 완료:**
- [x] 착수 전 사용자에게 확인받은 설계 결정: 기존 `payroll_calculator.py`는 "한 달 내내 단가 하나"를 가정하는데(4대보험 가입 요건이 "월 8일 이상" 같은 월 단위 합산 조건이라 하루씩 쪼개서 계산하면 오히려 틀어짐), 월중 단가변경이 실무상 없다는 사용자 확인을 받아 그 가정을 그대로 유지하기로 함. 대신 대상월에 적용할 단가가 아예 없는 경우엔 `calc_status='held'`로 보류(기획서 6.4/10번의 held 취지를 "단가 없음" 케이스로도 확장 적용).
- [x] `payroll_results` 테이블(worker_id, target_month, work_days, 세목별 금액, calc_status, `UNIQUE(worker_id, target_month)`) — Alembic 마이그레이션 적용 완료.
- [x] `POST /api/payroll/recalculate?month=`: 해당월에 출역(is_present=true) 기록이 있는 근로자만 대상으로, ①임시등록자(provisional)면 held, ②단가가 없으면 held, ③둘 다 있으면 `payroll_calculator.calculate_payroll()` 호출해 세목별 계산 후 `payroll_results` upsert(재실행해도 중복 안 생김).
- [x] `GET /api/payroll?month=`: 저장된 `payroll_results` 조회(단순 리스트).
- [x] pytest 6개 추가(`test_payroll_service.py`: ok/held(임시등록)/held(단가없음)/기간필터링/재계산멱등성/조회) — 전체 43개 통과.
- [x] curl E2E 검증 완료 — 실제 데이터로 재계산 2회 실행(단가 등록 전=held → 단가 등록 후=ok로 전환 확인), 세금 계산값(고용보험 1,440원, 순지급액 158,560원)이 수식과 정확히 일치함을 확인.
- [x] 4번 완료 직후 "다음이 프런트엔드가 맞는지" 재점검 요청 받아 기획서 원문 재확인 — 개발순서(1~10번) 자체는 여전히 정확했지만, 중요한 재발견: 기획서 3장(MVP 범위) 2번 항목에 "일일 출역 입력은 PDF검수화면과 수동입력이 같은 화면"이라고 명시돼 있고 12번 각주에도 "수동 입력 화면이 검수 화면을 겸하므로 먼저 완성돼야" 한다고 돼 있어서, 사실 2번(근로자마스터)·3번(출역)도 원래는 "화면"까지 포함하는 단계였음. 이 세션까지 2·3·4번을 전부 API만 구현하고 화면은 미룬 상태였다는 걸 사용자에게 보고 → 사용자가 "화면 4개(로그인/근로자마스터/출역입력/명세서)를 한번에 스캐폴딩 범위로 잡아라"고 확정.

**프런트엔드(React/Vite) 스캐폴딩 — 2026-07-20 세션에서 착수+완료:**
- [x] `frontend/` 폴더에 Vite+React+TypeScript 생성(`npm create vite@latest frontend -- --template react-ts`), `react-router-dom` 추가. javascript.md 규칙대로 `src/{components,pages,hooks,context,services,utils}` 구조.
- [x] `src/services/apiClient.ts`: fetch 래퍼(JWT 토큰 자동 첨부, RFC7807 에러를 `ApiError`로 변환, FormData 자동 감지로 Content-Type 분기).
- [x] `src/context/AuthContext.tsx` + `ProtectedRoute`: 토큰은 `localStorage`에 저장, 미인증 시 `/login`으로 리다이렉트.
- [x] 화면 4개 구현: `LoginPage`(관리자 로그인), `WorkersPage`+`WorkerDetailPanel`(검색/등록/상세수정/정식전환), `AttendancePage`(현장·날짜 선택, 출역 일괄입력/저장, 전일복사), `PayrollPage`(월 선택, 재계산, 세목별 결과 테이블 + 면책문구).
- [x] `frontend/.env`(`VITE_API_BASE_URL=http://localhost:8000/api`, `.gitignore`에 추가) + `.env.example`.
- [x] 검증: `tsc -b` 타입체크 통과, `npm run build` 프로덕션 빌드 성공, `npm run dev`로 실제 기동 후 `curl`로 index.html 200 확인, 백엔드 CORS 프리플라이트(`Origin: http://localhost:5173`)가 정상 허용됨을 확인. API 응답 필드명은 이번 세션에서 이미 curl로 검증했던 실제 응답과 프론트 TS 타입을 전부 대조함.
- [x] **브라우저 실검증 일부 완료**: 사용자가 직접 `http://localhost:5173`에서 구글 로그인까지는 확인함(아래 로그인 전환 섹션 참고). 근로자 등록→출역 입력→재계산→명세서까지 전체 골든패스는 아직 클릭 검증 안 됨 — 다음 세션 시작 지점.
- [ ] 신분증/통장 파일 업로드 UI는 아직 없음(백엔드 API는 있음) — 필요시 추가.
- [ ] 프런트엔드 자동화 테스트(React Testing Library 등) 없음 — testing.md 규칙상 필요하면 다음에 추가.

**관리자 로그인 방식 전환(비밀번호 → 구글/MS OAuth) — 2026-07-20 세션에서 진행:**
- 사용자 요청으로 착수: 회사가 구글·MS 계정을 모두 쓰므로 관리자 로그인을 아이디/비밀번호 대신 구글/MS 로그인으로 전환. 결정 2건(사용자 확인): ① 기존 비밀번호 로그인은 완전히 제거(폴백 없음), ② 관리자 인가는 도메인 전체 허용이 아니라 **화이트리스트(사전 등록된 이메일만)** 방식.
- [x] `users` 테이블을 `username/password_hash` → `email`(unique) 화이트리스트로 전환. Alembic 마이그레이션 시 기존 로컬 admin 행은 임시 이메일로 백필 후 실제 이메일로 재설정.
- [x] `app/core/oauth.py` 신설: 구글/MS ID 토큰을 각 provider의 JWKS 공개키로 서명 검증 + issuer(MS는 테넌트 무관 패턴 매칭)/audience 확인 후 이메일 추출. **서버에 client secret 불필요**(ID 토큰 서명 검증만 하는 순수 OIDC 흐름이라 client ID만 있으면 됨).
- [x] `POST /api/admin/login/google`, `POST /api/admin/login/microsoft` — `{id_token}`을 받아 검증 후 화이트리스트 대조, 통과하면 기존과 동일한 자체 세션 JWT 발급. 기존 `POST /api/admin/login`은 삭제.
- [x] `scripts/seed_admin.py`를 `<email> <name>`으로 변경(비밀번호 없음).
- [x] `backend/.env`/`.env.example`, `frontend/.env`/`.env.example`에 `GOOGLE_CLIENT_ID`/`MICROSOFT_CLIENT_ID`(프론트는 `VITE_` 접두사) 추가.
- [x] 프런트엔드: `@react-oauth/google`(구글 버튼), `@azure/msal-browser`(MS 팝업 로그인, `@azure/msal-react`는 불필요해서 제외) 추가. `LoginPage`를 OAuth 버튼 방식으로 전면 교체.
- [x] 백엔드 테스트 재작성: `test_auth.py`(세션 JWT), 신규 `test_oauth.py`(테스트용 RSA 키+가짜 JWKS 클라이언트로 서명검증 로직 9개), 신규 `test_auth_service.py`(화이트리스트 통과/거부 4개) — 전체 55개 통과.
- [x] **구글 로그인 실제 검증 완료**: Google Cloud Console에서 사용자가 만든 실제 Client ID(`718142738089-alt499...apps.googleusercontent.com`)를 양쪽 `.env`에 반영, 관리자 화이트리스트에 `a07089201008@gmail.com` 등록 후 브라우저에서 실제 로그인 성공 확인.
- [ ] **MS 로그인은 보류**: 사용자가 "일단 이렇게만 하고 넘어가자, 추후에 다시"라고 결정 — 코드는 구현·단위테스트까지 끝났지만, Azure(Microsoft Entra ID) App registration이 아직 없어 `MICROSOFT_CLIENT_ID`가 플레이스홀더 상태(`REPLACE_WITH_REAL_MICROSOFT_CLIENT_ID`)임. 실제 로그인 시도하면 지금은 실패함 — 다음에 Azure Portal에서 App registration 만들고 Client ID 받아서 반영 필요.
- **재발 방지 메모**: 이번 세션에 코드만 바꾸고 uvicorn 재시작을 깜빡해서 "구글 로그인 401" 오류가 났었음(옛날 라우트가 떠있었음) — 백엔드 코드 변경 후에는 항상 uvicorn 재시작 확인할 것.

---

## 6. 파일 & 리소스 위치

```
프로젝트 폴더 (C:\Users\위즈팩토리\Desktop\노무비-관리-시스템\)
├── .claude/                          # 프로젝트 설정 (스킬 27개, 훅, 규칙)
├── backend/                           # FastAPI 백엔드 (신규, 2026-07-16 시작)
│   ├── app/services/payroll_calculator.py  # 기획서 6.2 계산 로직
│   ├── app/routers/{workers,rates,sites,attendance,payroll,auth}.py
│   ├── app/core/oauth.py             # 구글/MS ID 토큰 검증
│   ├── tests/                        # pytest 55개(계산/근로자/단가/출역/정산/인증/OAuth)
│   └── pyproject.toml
├── frontend/                          # React+Vite 프런트엔드 (신규, 2026-07-20 시작)
│   ├── src/pages/{LoginPage,WorkersPage,AttendancePage,PayrollPage}.tsx
│   ├── src/services/{apiClient,msalClient}.ts, src/context/AuthContext.tsx
│   └── .env(로컬 전용, git 미포함)/.env.example
├── samples/                          # 검증 샘플 파일
│   ├── 노무비 예시.xlsx               # 캐시된 계산값 있음 — 회귀 테스트 기준
│   └── 노무비_테스트.xlsx             # 캐시값 없음(재계산 안 됨), 검증엔 미사용
├── archive/
│   └── 구형_LibreOffice검증_20260714/  # 폐기된 접근 검증 스크립트 8개 + README
└── HANDOFF.md                        # 이 파일

기획서 (최신, 2026-07-16)
└── C:\Users\위즈팩토리\Desktop\새 폴더\기획서\노무비_관리_시스템_기획서.md

기타 새 폴더 하위
├── 프롬포트/
└── 하루 마무리/
```

---

## 7. 메모리 및 규칙

- 📝 코드 언어 규칙 저장됨 → `~/.claude/projects/C--Users------/memory/feedback_code_language.md`
- 🎯 기획서는 확정 단계 — 다음은 계산 로직 구현 + 실측 검증

---

## 8. 다시 시작할 때 체크리스트

```
[ ] 최신 기획서 확인: 새 폴더/기획서/노무비_관리_시스템_기획서.md (날짜 확인 — 더 최신판 있는지)
[ ] 프로젝트 폴더 확인: /Desktop/노무비-관리-시스템/
[ ] backend/ 테스트 통과 확인: cd backend && ./.venv/Scripts/python.exe -m pytest tests/ -v (68개 통과 기대)
[ ] docker compose -p labor-cost up -d postgres minio (컨테이너 재기동, 데이터는 볼륨에 유지됨)
[ ] uvicorn app.main:app --reload 로 로컬 기동 후 /api/health 로 DB 연결 확인 (MinIO 버킷은 lifespan에서 자동 생성됨)
[ ] cd frontend && npm run dev 로 기동 후 http://localhost:5173 접속, 구글 로그인으로 확인
[ ] ⚠️ **코드 변경 후엔 uvicorn --reload를 믿지 말 것** — Windows에서 리로드가 조용히 실패함(2026-07-22 반복 확인). 반드시 프로세스 kill + 재시작 + curl로 실제 응답 재확인. (CLAUDE.md에도 규칙 있음)
[ ] **가장 먼저 할 일: 기획서 12번 6번 — 양식 업로드 + 셀 매핑 화면** (샘플 `samples/노무비 예시.xlsx` + 기획서 7번 셀 위치표로 바로 착수 가능). 그 뒤 7번(제출용 엑셀 생성).
[ ] (아직 안 한 브라우저 검증) 근로자등록→출역입력→정산재계산 골든패스 실제 클릭 검증 — 2026-07-22에 API/curl로는 검증했으나 전체 클릭 골든패스는 사용자가 직접 확인 필요
[ ] MS 로그인 이어서 하려면: Azure Portal에서 App registration 만들고 Client ID를 backend/.env, frontend/.env의 MICROSOFT_CLIENT_ID에 반영
[ ] PDF 자동기입(기획서 12번 8번)은 실제 명단 PDF 샘플 확보 전까지 보류 유지
[ ] (선택) 출역 `attendance_records.trade` 스냅샷 컬럼 제거 — 이제 표시엔 안 쓰이나 미래 코드 실수 방지용
[ ] 코드 언어 규칙 확인 (영어 식별자, 한글 주석)
[ ] 팀 하네스는 만들어져 있음(.claude/workflows/feature-plan.js, feature-build.js) — 단 기본은 직접 작업, 사용자가 명시적으로 "워크플로우로"라고 할 때만 실행(토큰 비용 이유)
```

---

**최종 상태 (2026-07-20 세션 종료 시점):** 근로자 마스터(2번) + 일일 출역 입력(3번) + payroll_results 계산 파이프라인(4번) + 웹 명세서 화면(5번, 프런트엔드 스캐폴딩) 전부 완료. 근로자/단가/현장/현장이동이력/출역/정산 API 전부 curl E2E 검증(한글 payload 포함, 실제 세금계산값 수식과 일치 확인), MinIO 버킷 자동생성 버그 수정, 현장이동이력 쓰기 로직 신규 구현. 관리자 로그인을 비밀번호 방식에서 구글/MS OAuth(화이트리스트)로 전면 전환 — 구글 로그인은 실제 Client ID로 브라우저 검증까지 완료, MS는 코드/테스트만 끝내고 Azure 앱 등록은 보류. 유닛/통합 테스트 총 55개 통과. React+Vite 프런트엔드(로그인/근로자마스터/출역입력/명세서 4개 화면) 신규 구축. Git Bash 한글 인코딩 우회법 확정. 개발 순서(기획서 12번)를 원문과 두 차례 재대조해 어긋남 없음을 확인함.

---

## 6. 2026-07-21 세션 — 공정(trade) 리팩터링 + 실사용 검수로 발견한 공백들

**배경:** 지난 세션 프런트엔드를 브라우저로 실제 써보려다, 실제 출역 명단(사진) 기반 설계 변경(바탕화면 `progress.md`)을 먼저 반영해야 함이 드러남. 이후 세션 후반은 사용자가 화면을 직접 눌러보며 공백/버그를 실시간 보고 → 수정하는 흐름으로 진행.

**완료 (전부 검증됨 — pytest 57개 통과, npm run build/lint 통과):**
- **공정(trade) 리팩터링 (progress.md 설계 변경 반영)**:
  - 결정 근거: 실제 공정은 현장마다 최대 6개(관리자/장판/설비/실리콘/도배/직영). ①공정은 마스터 테이블 없이 자유텍스트 ②근로자 1명=프로젝트 기간 내내 공정 고정 → 단가는 여전히 근로자당 하나로 충분 ③출역 입력 화면은 원본 양식과 같은 "공정별 열 그리드".
  - 백엔드: `workers.trade` 컬럼 추가 + Alembic 마이그레이션 `8bf78b7d2c1c`(생성·적용 완료). `GET /api/sites/{site_id}/trades`(현장 배정 근로자들의 distinct 공정, 자동완성용) 신규. 출역 저장은 공정을 따로 안 받고 근로자의 고정 `trade`를 복사(`AttendanceEntryInput`에서 trade 제거). 깨진 테스트 5개 수정 + `test_site_service.py` 신규.
  - 프런트: `types.ts` trade 필드, `WorkersPage`(등록폼/목록 공정), `WorkerDetailPanel`(공정 입력 + 현장기준 `<datalist>` 자동완성), `useTrades` 훅 신설, `AttendancePage` 리스트형→**공정별 열 그리드**로 전면 재구성.
- **`CLAUDE.md` 프로젝트 루트에 신규 생성** (`/init`) — 실행/테스트 명령, Windows 이슈 3종, 계층구조·인증흐름·PII·계산엔진 배경·데이터 불변식.
- **팀 하네스 신규**: `.claude/workflows/feature-plan.js`(기획→엔지니어/스켑틱 검토→합성), `feature-build.js`(구현→코드/보안 리뷰→보완→검증, 실패 시 재보완). 기존 커스텀 에이전트(planner/architect/code-reviewer/security-reviewer) 재활용. **단 실사용은 토큰 비용 이유로 보류 — 기본은 직접 작업, 명시적 요청 시에만 실행**(메모리 `feedback_workflow_token_cost` 등록).
- **실사용 UX 공백 2건 수정**: ①현장 추가 화면이 없던 문제 → `WorkerDetailPanel` 현장 드롭다운에 "+ 새 현장 추가..." 인라인 폼(`useSites.createSite` 추가). ②출역입력 "근로자 추가"가 전체 근로자를 다 보여주던 버그 → 선택 현장 소속만 필터 + 안내 문구.

**진단 + 방식 확정만 하고 구현은 다음 세션으로 넘긴 3건 (⬅ 다음 세션 최우선):**
1. **일일출역 "제거"가 DB 반영 안 됨** — `save_daily`가 upsert만 하고 삭제를 안 함, 삭제 경로 자체가 없음. **확정 방식**: "제거 후 저장하면 화면 그대로 반영"(일괄저장 시 그 site+date에서 화면에 없는 기록은 삭제하는 reconcile). ※에러 메시지 개선(충돌 시 UUID→근로자 이름)만 `attendance_service._upsert_entry`에 미리 반영해둠, 실제 삭제 로직은 아직 없음.
2. **이름이 영어(UUID)로 섞여 보임** — 출역/명세서 응답에 `worker_id`만 있고 이름은 프런트가 `/workers` 목록과 매칭, 매칭 실패 시 `?? worker_id`로 UUID 노출. **확정 방식**: 출역/명세서 응답에 `worker_name` 직접 포함 → fallback 자체 제거. (DB의 이름은 전부 한글로 정상 저장돼 있음 — 순수 표시 버그)
3. **노무비 단가 입력 메뉴 없음** — 백엔드 단가 API(`/workers/{id}/rates`)는 완비인데 프런트 화면만 없음. **확정 방식**: 근로자 상세(WorkerDetailPanel)에 "노무비 단가" 하나만 입력(현재 단가 하나만, 기간은 자동 처리 — progress.md "단가는 근로자당 하나로 충분" 결정과 일치).

**다음 세션 시작 지점:** 위 3건 구현(단가 입력 UI / 출역 제거 reconcile / 응답에 worker_name) → 브라우저 골든패스 실검증 → 기획서 12번 6번(양식 업로드+셀 매핑). MS 로그인은 사용자가 Client ID 줄 때 마저 연결. PDF 자동 업로드(8번)는 실제 샘플 파일 확보 전까지 보류로 이미 결정됨.

---

## 7. 2026-07-22 세션 — 미룬 3건 구현 + 실사용 검수 버그 + UX 개편 + 명세서 공정/날짜 조회

**⚠️ 이 세션 최대 교훈 (반복 함정):** Windows에서 `uvicorn --reload`가 파일 변경을 감지만 하고 **실제 리로드는 조용히 실패**하는 일이 두 번 발생. 이 때문에 "고쳤는데 반영 안 됨" 증상(정식전환 실패 / [object Object] / 주민번호 형식)이 반복됨. → **코드 변경 후엔 리로드를 믿지 말고 프로세스 kill + 재시작 + curl로 실제 응답 재확인**. 이 원칙은 프로젝트 루트 `CLAUDE.md`에도 추가됨.

**지난 세션 미룬 3건 — 전부 완료:**
- **응답에 worker_name 포함**: `AttendanceRecordResponse`/`PayrollResultResponse`에 `worker_name` 추가, 서비스에서 채움. 프런트 `?? worker_id` UUID fallback 완전 제거.
- **일일출역 "제거" reconcile**: `save_daily`가 upsert만 하던 것 → 화면(payload.entries)에 없는 그 site+date 기록은 삭제. 전원 제거(빈 명단 저장) 허용(`AttendanceDailySaveRequest.entries` min_length 제거), 프런트 저장 가드도 완화. `attendance_repository.delete_record` 추가.
- **노무비 단가 입력 UI**: `WorkerDetailPanel`에 단가 등록/수정 폼(`frontend/src/hooks/useWorkerRate.ts` 신설). 백엔드 `/workers/{id}/rates`는 기존 완비.

**"이름만으로 임시 등록" 스펙 위반 수정 (신규 발견):**
- 원인: `workers.birth_date`가 DB `NOT NULL` + 스키마 필수라 기획서 3장 "이름만으로 임시 등록" 위반.
- 수정: 마이그레이션 `8bc00b59c578`(birth_date nullable) + `WorkerCreateRequest`/`WorkerResponse` optional + **정식전환 요건(`_has_activation_requirements`)에 birth_date 추가**(생년월일 없이 정식전환 시 `calculate_age` 크래시 방지). `WorkerDetailPanel`에 생년월일·이름 편집 필드 추가. OpenAPI 계약도 갱신.

**검증 에러 한글화:**
- FastAPI 기본 422(영어 배열 detail)가 그대로 노출되던 것 → `app/core/exceptions.py`에 `validation_error_handler` 전역 등록, "name: 필수 항목입니다" 식 한글 변환. `frontend/src/services/apiClient.ts`도 배열/객체 detail 방어("[object Object]" 재발 방지). `backend/tests/test_exceptions.py` 신규.

**실사용 검수로 잡은 버그:**
- **정식전환 안 됨**: 원인은 주민등록번호 미입력 + 서버 미재시작(리로드 실패). 코드 문제 아님.
- **주민번호 형식 강제 제거**: 서류 확보 전 임시값 허용 위해 정규식(`RESIDENT_REGISTRATION_NUMBER_PATTERN`) 검증 삭제. 계좌번호는 원래 제한 없었음.
- **AttendancePage `limit=200` 버그**: 백엔드 상한이 100(`le=100`)이라 매번 422 → "근로자 추가" 드롭다운이 늘 비어 있었음. `limit=100`으로 수정.

**UX/UI 전면 개편 (사람인류 톤, `/frontend-design`):**
- 네이비 헤더+블루 액센트 기업형 톤, **좌측 세로 사이드바**로 전환(상단 가로→마우스 이동 줄임), 전체 스케일 약 30% 확대, 콘텐츠 최대폭 확장.
- 명세서 가독성 강조: 차감지급액 컬럼 파란 배경+큰 글씨, 짝수 행 줄무늬, 합계 강조, 숫자 고정폭(IBM Plex Mono) 정렬. 폰트: Gothic A1 + IBM Plex Mono.

**명세서 공정별 조회 + 근로자 날짜별 상세 (기획서 "조회는 MVP 범위" 반영):**
- 명세서 응답에 `trade` 포함(`worker_repository.get_name_trade_by_ids`). 프런트에 공정별 카드(인원/공수/금액) + 클릭 필터(`PayrollPage`).
- `GET /api/attendance/worker-monthly?worker_id=&month=` 신규 — 현장 무관 근로자 월 전체 출역 + 현장명(`site_repository.get_names_by_ids`, `attendance_repository.list_worker_month`). 명세서 행 클릭 시 `WorkerMonthlyDetail` 패널.

**"유령 명세서" 버그 수정:**
- 증상: 없어야 할 사람이 명세서에 뜨고 재계산하면 사라짐. 원인: 출역 삭제됐는데 `payroll_results` 행 잔존, GET은 테이블 전체 반환.
- 수정: `recalculate_month`가 그 달 출역 없는 근로자 결과를 먼저 삭제(`payroll_repository.delete_results_except`).

**김성진 "미분류" — 공정 표시 일관화:**
- 원인: 출역 먼저 입력(공정 미지정) 후 공정 지정 → 출역 기록 `trade` 스냅샷이 빈 채로 박제.
- 수정: 출역/명세서/날짜별 상세 **모든 조회에서 출역 스냅샷 대신 근로자 현재 `worker.trade`** 사용으로 통일. `attendance_service._to_response`/`_summarize`가 응답의 trade 기준으로 동작.
- **남은 리스크(투명):** `attendance_records.trade` 스냅샷 컬럼은 아직 존재(표시엔 안 씀). 미래 코드 실수 방지 위해 다음에 마이그레이션으로 제거 권장.

**문구/명명 정리:**
- 로그인 "화이트리스트..." 문장 제거, 날짜별 상세 "현장을 넘나든..." 제거, 명세서 상단 요약 카드 제거(표 합계와 중복), "면책 문구:" 라벨 제거(안내 문장 유지).
- 메뉴/제목: "근로자 마스터"→**근로자 입력**, "웹 명세서"→**명세서**.

**검증:** pytest **68개 통과**(신규: 이름만 등록/birth_date 정식전환 게이트/출역 reconcile 삭제·빈명단/worker_name/검증에러 한글/stale 정리/trade 포함/근로자 월별 상세). `tsc -b`/`npm run build`/`npm run lint`/Redocly lint 통과. 신규 마이그레이션 `8bc00b59c578`.

**다음 세션 시작 지점:** 기획서 12번 **6번(양식 업로드 + 셀 매핑 화면)** — 샘플 `노무비 예시.xlsx` + 기획서 7번 셀 위치표로 바로 착수 가능. 그 뒤 7번(제출용 엑셀 생성). 8번(PDF 자동기입)은 실 샘플 확보 전까지 보류. MS 로그인은 Azure Client ID 받으면 연결. (선택) 출역 `trade` 스냅샷 컬럼 제거.
