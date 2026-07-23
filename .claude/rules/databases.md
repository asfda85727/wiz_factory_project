# 데이터베이스 — PostgreSQL, MongoDB, Redis

## PostgreSQL
- 항상 마이그레이션 사용 (Java는 Flyway, Python은 Alembic). 프로덕션에서 스키마를 수동 수정하지 말 것.
- WHERE, JOIN, ORDER BY에 쓰는 컬럼에 인덱스 생성. `EXPLAIN ANALYZE`로 확인.
- 모든 PK는 `UUID`(Python `uuid4` 기본값). `BIGSERIAL` 사용 금지 — 개인정보를 다루는 소규모 내부 툴이라 ID enumeration 방지를 단순하게 우선한 프로젝트 결정.
- 모든 날짜/시간 컬럼은 `TIMESTAMPTZ` (NOT `TIMESTAMP`).
- Connection pooling 사용 (Java는 HikariCP, Python은 asyncpg pool).
- 다중 문장 작업은 transaction 사용. 트랜잭션은 짧게.
- `JSONB` 컬럼은 최소한으로 — 진정한 스키마리스 데이터만. JSON 필드를 자주 조회하면 컬럼으로 추출.
- 네이밍: 테이블과 컬럼은 `snake_case`, 테이블명은 복수형 (`users`, `orders`).

## MongoDB
- 정규화가 아닌 접근 패턴 중심으로 문서 설계. 함께 읽는 데이터는 embed.
- Embed 사용: 1:1 또는 1:few 관계, 데이터가 함께 읽혀짐, 자식 데이터가 무한정 증가하지 않음.
- Reference 사용: 1:many 또는 many:many, 데이터가 독립적으로 변경, 문서 크기가 16MB에 근접.
- 항상 쿼리 패턴에 맞는 인덱스 생성. 다중 필드는 compound 인덱스.
- 문서 구조 강제는 `$jsonSchema` 스키마 검증.
- `_id`는 `ObjectId`. 모든 컬렉션에 `createdAt`, `updatedAt` timestamp 추가.
- 복잡한 쿼리는 aggregation pipeline. `$where`와 JS 실행 금지.

## Redis
- 올바른 데이터 구조 사용: cache는 Strings, 객체는 Hashes, 유일성은 Sets, 랭킹/타임라인은 Sorted Sets, 큐는 Lists.
- 캐시 항목에 항상 TTL 설정. 의도한 경우 외엔 영구 키 금지.
- 키 네이밍: `service:entity:id:field` (예: `myapp:user:123:profile`).
- 대량 작업은 pipelining. 원자적 다단계 작업은 Lua 스크립트.
- 캐시 패턴: Cache-Aside (읽기), Write-Through (쓰기), Write-Behind (비동기 쓰기).
- 잃어도 괜찮은 데이터만 Redis에 저장 (persistence + replicas 사용하지 않는 경우).
- 프로덕션에서 `KEYS` 대신 `SCAN` 사용. `KEYS`는 서버를 블로킹함.

## 크로스 DB 가이드라인
- 각 서비스는 자신의 데이터 소유. 서비스 간 공유 DB 금지.
- 작업에 맞는 DB 선택: 관계형/트랜잭션은 PostgreSQL, 문서/유연한 스키마는 MongoDB, 캐시/세션/실시간은 Redis.
- 연결 실패는 항상 재시도와 circuit breaker로 graceful 처리.
- 느린 쿼리 로깅. 쿼리 latency 임계값 초과 시 알림 설정.
