# 테스트

## 커버리지 목표
- 비즈니스 로직 최소 80% 코드 커버리지.
- 핵심 경로 100% 커버리지 (인증, 결제, 데이터 변경).

## 테스트 유형
- **단위 테스트**: 격리, 빠름, 외부 의존성 mocking. 모든 서비스 메서드마다.
- **통합 테스트**: 실제 DB 상호작용, API 엔드포인트, 메시지 컨슈머 테스트.
- **E2E 테스트**: 핵심 사용자 흐름만. 과다 투자 금지 — 느리고 brittlе함.

## TDD 워크플로우
1. **RED** — 원하는 동작을 정의하는 실패 테스트 작성.
2. **GREEN** — 테스트를 통과시키는 최소 코드 작성.
3. **IMPROVE** — 테스트 유지하면서 리팩토링.

## 스택별 도구
- **Java/Spring Boot**: JUnit 5 + Mockito. 통합 테스트는 `@SpringBootTest`. 실제 DB/Redis/Kafka 테스트는 Testcontainers.
- **Python/FastAPI**: `pytest` + `pytest-asyncio`. API 테스트는 `httpx.AsyncClient`. Mocking은 `unittest.mock` 또는 `pytest-mock`.
- **JavaScript/Express**: Jest 또는 Vitest. API 테스트는 `supertest`.
- **React**: React Testing Library. 구현이 아닌 동작 테스트. 내부 상태 테스트 금지.

## 테스트 네이밍
- 시나리오와 예상 결과 설명.
- Java: `shouldReturnUserWhenIdExists()`, `shouldThrowWhenEmailInvalid()`
- Python: `test_returns_user_when_id_exists()`, `test_raises_when_email_invalid()`
- JS: `it('returns user when id exists')`, `it('throws when email is invalid')`

## 규칙
- 테스트는 독립적. 테스트 간 공유 mutable 상태 금지.
- 테스트에서 sleep 금지. awaitility (Java), polling, 또는 async assertions 사용.
- Flaky 테스트는 즉시 수정. Flaky 테스트는 없는 것보다 나쁨.
- 프레임워크 코드는 테스트하지 말 것. 자신의 로직만 테스트.
- 외부 서비스(HTTP 호출, 서드파티 API) mocking. DB는 Testcontainers 또는 내장 서버 사용.
