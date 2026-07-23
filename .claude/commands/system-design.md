---
description: System design discussion and diagramming
---

# System Design

Help me think through the system design for: $ARGUMENTS

## Framework

Walk through these areas step by step. Ask me clarifying questions at each step before moving on.

### 1. Requirements
- What are the functional requirements?
- What are the non-functional requirements (latency, throughput, availability, consistency)?
- What scale are we designing for? (users, requests/sec, data volume)

### 2. High-Level Architecture
- What are the main components/services?
- How do they communicate (sync REST/gRPC vs async Kafka/queues)?
- Draw the architecture using text diagrams.

### 3. Data Design
- What data needs to be stored?
- SQL vs NoSQL decisions for each entity (and why).
- Schema design, indexing strategy, partitioning/sharding if needed.

### 4. API Design
- Key endpoints between services and to clients.
- Authentication and authorization approach.

### 5. Scaling & Performance
- Where are the bottlenecks?
- Caching strategy (what, where, TTL, invalidation).
- Database read replicas, connection pooling, query optimization.
- Horizontal scaling approach.

### 6. Reliability
- Single points of failure and how to eliminate them.
- Failure modes and graceful degradation.
- Monitoring, alerting, circuit breakers.

## Rules
- Explain trade-offs for every decision (e.g., "CP vs AP", "SQL vs NoSQL for this use case").
- Use real numbers when estimating (requests/sec, storage in GB, latency in ms).
- Reference technologies I know: Spring Boot, FastAPI, PostgreSQL, MongoDB, Redis, Kafka, Flink, Docker, K8s.
- This is a learning exercise — teach me the reasoning, not just the answer.
