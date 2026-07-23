# wiz_factory_project

# 노무비 관리 시스템

건설 현장 노무비를 관리자가 입력하고, 세금·4대보험을 자동 계산해 원청(LH) 제출용 엑셀 양식을 생성하는 내부 관리 시스템입니다.

## 배경

현재는 다음과 같은 흐름으로 노무비를 처리하고 있습니다.

```
TBM 종이 서명 → 한글파일 수기 입력 → 관리자 전달
→ 엑셀 서식(명세서_철거 등)에 재입력해 노무비·세금·차감지급액 계산
→ 매월 원청(LH) 제출
```

같은 정보가 세 번 손을 거치며 반복 입력되다 보니, 월 10회 이상의 수정/재작업이 발생하고 있습니다. 이 시스템은 서명 이후의 **반복 수기 입력 단계**를 제거하는 것이 목표입니다. (TBM 종이 서명 자체는 현장 안전관리상 필수 절차로 유지합니다.)

## 목표 사용자

| 역할 | 권한 |
|---|---|
| 관리자 (여러 명 발급 가능, 등급 구분 없음) | 현장 관리, 출역 입력, 단가 입력, 양식 매핑, 노무비 확인, 제출용 서식 생성 — 전원 동등하게 전체 현장/근로자 접근 |
| 근로자 | 본인 출역일수·노무비 조회만 (입력 권한 없음), 전화번호+주민번호 앞자리 + OTP 인증코드로 로그인 |

## 핵심 기능 (MVP)

| # | 기능 | 우선순위 |
|---|---|---|
| 근로자 마스터 데이터 | 인적정보 + **근로자당 단가 1개** (현장·공정 무관, 1인 1현장 원칙) | P0 |
| 근로자 전체 검색/조회 | 현장 구분 없이 전체 근로자 대상 검색, 현장 이동 시 재등록 없이 소속만 변경 | P1 |
| 일별 출역 입력 | PDF 명단 업로드(자동 추출+검수) 또는 수동 입력, 현재 선택한 현장 소속 인원만 표시 | P0 |
| 노무비/세금 자동 계산 | 국세청 표준 공식 기반 자체 계산 (아래 참고) | P0 |
| 양식 필드 매핑 | 원청 엑셀 양식에 시작 셀+반복 간격 입력(현장별 독립 매핑), 테스트 채우기 미리보기 | P1 |
| 월별 제출용 엑셀 생성 | 계산 결과를 매핑된 셀에 값으로 채워 생성 | P0 |
| 관리자 대시보드 | 현장별 출근 인원, 세전·세후 노무비 합계, 서류 미비자 목록 | P1 |
| 근로자 셀프 조회 | 전화번호+주민번호 앞자리 입력 → OTP 인증코드 확인 후 조회 (읽기 전용) | P1 |

## 노무비 계산 방식

세금·4대보험은 원청 엑셀의 함수를 그대로 이용하지 않고, **국세청·4대보험공단이 공개한 표준 공식을 시스템이 직접 계산**합니다. 계산된 값은 원천 데이터와 함께 원청 제출 양식의 매핑된 셀에 값으로 채워 넣습니다.

| 항목 | 기준 | 비고 |
|---|---|---|
| 소득세(갑근세) | (일당 − 15만원) × 6% × 45% | 일 단위, 나이 무관 |
| 지방소득세(주민세) | 소득세 × 10% | 10원 단위 절사 |
| 고용보험 | 일당 × 0.9% | 만 65세 이후 신규 채용자는 미적용 |
| 국민연금 | 기준소득월액 × 4.75% | 만 18~60세, 월 8일 이상 근무 시 가입 대상. **국세청·국민연금공단 공식 기준율 그대로 적용으로 확정** |
| 건강보험 | 보수월액 × 3.595% | 나이 무관, 월 8일 이상 근무 시 가입 대상 |
| 장기요양보험 | 건강보험료 × 13.14% | 건강보험 가입자에 연동 |

> 요율은 매년 바뀌므로 코드에 하드코딩하지 않고 `insurance_rates` 테이블에서 연도별로 관리합니다. **소액부징수(소득세 1,000원 미만 미징수)·세목별 반올림/절사 규칙은 개발 1단계 검증 대상으로 남아 있습니다.** 실제 신고·납부 전에는 세무/노무 전문가 검토를 권장합니다.

## 기술 스택

| 영역 | 선택 |
|---|---|
| 백엔드 | Python (FastAPI) |
| 프론트엔드 | React (Vite, SPA) — 1인 개발 + 로그인 뒤에만 존재하는 내부 도구라 SSR 불필요 |
| DB | PostgreSQL |
| 파일 저장 | S3 호환 오브젝트 스토리지 (AWS S3 / MinIO) |
| 엑셀 생성 | openpyxl |
| 명단 PDF 파싱 | pdfplumber (표 추출) / PyMuPDF (텍스트 추출) — 한글에서 내보낸 텍스트 기반 PDF, 추출 실패 시 AI비전/수동 폴백 |
| 배포 | Docker Compose (프론트 정적 산출물은 Nginx 컨테이너로 서빙) |

민감정보(주민등록번호, 계좌번호)는 DB 암호화와 별개로 애플리케이션 레벨에서 AES-256-GCM으로 암호화 후 저장합니다.

## 데이터 모델 개요

```
users                관리자 계정 (role 전부 'admin' 통일, 등급 구분 없음)
sites                현장 = 프로젝트/계약 단위 (지역 라벨 아님), client_name/start_date 포함
workers              근로자 (생년월일, 암호화된 주민번호/계좌번호, current_site_id 등)
site_assignment_log  현장 이동 이력
worker_rates         근로자당 단가 1개 (현장·공정 무관), 변경 이력 관리
attendance_records   출역 기록 (일 단위, UNIQUE(worker_id, work_date) — 하루 1현장 강제)
attendance_audit_log 출역 수정 이력
insurance_rates      연도별 세금/4대보험 요율
payroll_results      월별 계산 결과 (세목별 상세 포함)
form_templates       원청 제출용 엑셀 양식 (site_id별 독립)
field_mappings       양식 필드-셀 매핑 (start_cell + row_interval 방식)
monthly_submissions  월별 제출 이력
```

## API 개요

| 영역 | 예시 |
|---|---|
| 인증 | `POST /api/admin/login`, `POST /api/worker/login`, `POST /api/worker/login/verify-otp` |
| 근로자 | `GET /api/workers?search=` (현장 무관 전체검색), `POST /api/workers`, `GET /api/workers/{id}/site-history` |
| 현장/단가 | `GET/POST /api/sites`, `POST/PATCH /api/workers/{id}/rates` |
| 출역 입력 | `GET /api/attendance/daily?site_id=`, `POST /api/attendance/import-pdf`, `POST /api/attendance/daily` |
| 양식 매핑 | `POST /api/templates` (site_id 지정), `POST /api/templates/{id}/mappings`, `POST .../mappings/test-fill` |
| 계산/제출 | `POST /api/payroll/recalculate?month=`, `POST /api/submissions/generate?month=` |
| 대시보드 | `GET /api/dashboard/summary?site_id=`, `GET /api/dashboard/missing-docs` |
| 근로자 조회 | `GET /api/me/attendance`, `GET /api/me/pay` |

## 시작하기

```bash
git clone <repo-url>
cd <repo-폴더>

# 환경변수 설정
cp .env.example .env

# 전체 스택 실행
docker compose up -d
```

## 개발 현황

현재 기획 단계

**진행 예정 순서**: 계산 로직·검증 → 근로자 마스터(전체검색 포함) → 일일 출역 입력 → payroll 계산 파이프라인 → 웹 명세서 화면 → 양식 업로드·매핑(테스트 채우기 포함) → 제출용 엑셀 생성 → 명단 PDF 자동 기입 → 대시보드 → 근로자 셀프 조회
