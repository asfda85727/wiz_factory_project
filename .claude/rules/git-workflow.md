# Git 워크플로우

## 커밋 형식
Conventional commits 사용: `<type>: <description>`

타입: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

예시:
- `feat: add user registration endpoint`
- `fix: handle null pointer in payment service`
- `refactor: extract email validation to shared util`

제목은 72자 이하. 필요하면 본문에 상세 내용 작성.

## 브랜치 전략
- `main` — 프로덕션 배포 가능, 항상 배포 가능한 상태.
- `dev` 또는 `develop` — 통합 브랜치 (사용할 경우).
- Feature 브랜치: `feat/short-description`, `fix/short-description`.
- 병합 후 브랜치 삭제.

## PR 프로세스
- PR은 집중된 범위. 기능 또는 버그 수정 1개씩.
- 요약 작성: 무엇이 바뀌었고 왜 바뀌었는지.
- 테스트 계획 또는 동작 증거 포함.
- 리뷰 요청 전에 diff 자체 검토.

## 워크플로우
1. `main`(또는 `dev`)에서 feature 브랜치 생성.
2. 작업하면서 작고 원자적인 커밋 작성.
3. 준비되면 push하고 PR 생성.
4. 리뷰 피드백은 새 커밋으로 반영 (리뷰 중 force-push 금지).
5. main으로 squash merge.

## 커밋하면 안 되는 것
- `.env` 파일, API 키, 비밀, 자격증명.
- IDE 설정 (`.idea/`, `.vscode/` - 팀이 공유하지 않는 경우).
- 빌드 산출물 (`target/`, `dist/`, `node_modules/`, `__pycache__/`).
- 큰 바이너리 파일.
