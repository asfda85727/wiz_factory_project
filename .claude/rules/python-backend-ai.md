# Python 백엔드 & AI/ML

## Python 표준
- Python 3.12. 모든 함수 시그니처에 Type hints.
- `@dataclass(frozen=True)` 또는 Pydantic `BaseModel`로 데이터 구조.
- `black`으로 포매팅. `ruff`로 린트. `mypy` 또는 `pyright`로 타입 체크.
- `logging` 모듈 사용, 프로덕션 코드에서 `print()` 금지.
- 가상 환경: `venv` 또는 `poetry`. 모든 의존성 pin.

## FastAPI 규칙
- 모든 요청/응답 스키마는 Pydantic 모델. 원본 dict 금지.
- 의존성 주입은 `Depends()` (DB 세션, 인증, 서비스).
- I/O-bound 작업은 비동기 엔드포인트 (`async def`). CPU-bound는 동기.
- 라우터는 도메인별로 구성: `routers/users.py`, `routers/orders.py`.
- 전역 예외 처리는 `@app.exception_handler()`.
- "fire-and-forget" 작업은 `BackgroundTasks` 사용.

## 프로젝트 구조
```
app/
  main.py           # FastAPI 앱, 미들웨어, 시작 이벤트
  config.py         # pydantic-settings로 설정
  routers/          # API 라우트 핸들러
  models/           # Pydantic 스키마 (요청/응답)
  services/         # 비즈니스 로직
  repositories/     # DB 접근
  core/             # 인증, 미들웨어, 예외
```

## DB 접근
- PostgreSQL: `SQLAlchemy 2.0` async + `asyncpg`, 또는 `SQLModel`.
- MongoDB: `motor` (async) 또는 `beanie` ODM.
- Redis: 비동기 접근은 `redis.asyncio`.
- 항상 connection pooling 사용. context manager로 세션 정리.

## AI/ML 패턴
- **RAG 파이프라인**: 문서 청킹(500-1000 토큰, 오버랩) → 임베딩 → 벡터 DB 저장 → top-k 검색 → 프롬프트 augment → 생성.
- **벡터 DB**: PostgreSQL + pgvector, 또는 전용 (Pinecone, Qdrant, Weaviate, ChromaDB). 메타데이터와 함께 임베딩 저장.
- **LLM 호출**: 가능하면 structured output(Pydantic 모델) 사용. temperature, max_tokens 명시. Rate limit은 exponential backoff로 처리.
- **프롬프트 엔지니어링**: 시스템 프롬프트는 파일에, 인라인 문자열 금지. 버전 관리.

## 에이전트 & MCP 패턴
- **ADK(Agent Development Kit)**: 도구는 typed 함수로 정의. 도구 설명은 간결하고 명확하게.
- **MCP 서버**: 각 서버 = 1개 기능 도메인. 도구 입/출력은 typed 스키마.
- **에이전트 아키텍처**: plan → execute → observe → reflect 루프. 폭주 방지로 반복 제한.
- **도구 설계**: 원자적, 가능하면 멱등, 구조화된 결과 반환.

## ML 모범 사례
- 학습, 평가, 추론 코드 분리.
- hyperparameter는 config 파일(YAML/TOML)로, 하드코딩 금지.
- MLflow, W&B 등으로 실험 로깅. 메트릭, 파라미터, 산출물 추적.
- 데이터 검증: 모델 추론 전 입력 shape, 타입, 범위 검증.
- 모델 버전 관리: 버전, 학습일, 데이터셋 해시로 태깅.
