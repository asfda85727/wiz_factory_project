# 인프라 — Docker, Kubernetes, Kafka, Flink

## Docker
- Multi-stage build로 이미지 크기 최소화. build와 runtime 단계 분리.
- 구체적 base image 태그 사용 (예: `eclipse-temurin:17-jre-alpine`), `latest` 금지.
- non-root 사용자로 실행. setup 후 `USER appuser` 추가.
- Dockerfile 레이어 순서: OS deps → app deps → source code (캐시 히트 최대화).
- `.dockerignore`로 `.git`, `node_modules`, `target/`, `__pycache__/`, `.env` 제외.
- 컨테이너당 1개 프로세스. 로컬 멀티 컨테이너는 docker-compose.
- 헬스 체크: `HEALTHCHECK` 명령어 추가 또는 compose/K8s에서 정의.

## Kubernetes
- stateless 앱은 Deployments. stateful 워크로드(DB)는 StatefulSets만.
- 모든 컨테이너에 resource requests AND limits 정의. unbounded pod 금지.
- 설정은 ConfigMaps, 민감한 데이터는 Secrets. env vars 또는 volume으로 mount.
- Liveness probe: 프로세스 살아있는가? Readiness probe: 트래픽 받을 수 있는가? Startup probe: 시작 느린 앱용.
- namespace로 환경 분리 (dev, staging, prod).
- Horizontal Pod Autoscaler (HPA) 기반 CPU/메모리 또는 custom 메트릭.
- 기본 rolling update. zero-downtime deploy는 `maxUnavailable: 0` 설정.
- 중요 서비스는 `PodDisruptionBudget` 사용.

## Kafka
- 토픽 네이밍: `<domain>.<entity>.<event>` (예: `orders.payment.completed`).
- 메시지 serialization은 Avro 또는 Protobuf + Schema Registry. 프로덕션에서 순수 JSON 금지.
- Partition key: 균등 분배하고 필요시 순서 유지 (예: user ID, order ID).
- Consumer groups: 논리적 consumer마다 1개 그룹. `enable.auto.commit=false`, 처리 후 commit.
- Idempotent consumer: at-least-once 설계. deduplication 또는 idempotency keys 사용.
- Retention: use case별로 토픽마다 설정. event sourcing = 길게, transient 이벤트 = 짧게.
- 재시도 후 실패한 메시지는 dead letter topic으로.
- 모니터링: consumer lag, under-replicated partitions, broker disk usage.

## Flink
- event-time 처리는 DataStream API. ProcessFunction은 꼭 필요할 때만.
- event-time window는 항상 watermark 설정. 늦은 데이터는 side output으로 처리.
- stateful 처리는 keyed state (ValueState, ListState, MapState). 불필요한 상태는 정리.
- Checkpointing: 합리적 간격(30초~5분)으로 활성화. RocksDB 백엔드로 incremental checkpoint.
- Exactly-once: checkpointing 활성화 + sink에서 Kafka transactions 사용.
- Backpressure: Flink UI로 모니터링. parallelism 확대 또는 느린 operator 최적화로 해결.
- Job 네이밍과 메트릭: 명확히 태깅. 비즈니스 로직 모니터링용 custom 메트릭 노출.
