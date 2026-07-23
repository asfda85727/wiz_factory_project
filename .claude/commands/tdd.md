---
description: Test-driven development workflow
---

# TDD Workflow

Implement the following using strict TDD: $ARGUMENTS

## Process

### 1. RED — Write Failing Tests First
- Define what the code should do via test cases.
- Cover the happy path, edge cases, and error cases.
- Run tests — they MUST fail. If they pass, the tests are wrong.

### 2. GREEN — Minimal Implementation
- Write the minimum code to make tests pass.
- No premature optimization. No extra features.
- Run tests — all must pass.

### 3. IMPROVE — Refactor
- Clean up the implementation while keeping tests green.
- Extract common logic, improve naming, simplify.
- Run tests again — still green.

## Stack-Specific Tools
- **Java/Spring Boot**: JUnit 5 + Mockito. Use `@SpringBootTest` for integration tests, Testcontainers for real DB.
- **Python/FastAPI**: pytest + pytest-asyncio. Use `httpx.AsyncClient` for API tests.
- **JavaScript**: Jest or Vitest. Use `supertest` for Express API tests. React Testing Library for components.

## Rules
- Never write implementation before a failing test exists.
- If you're unsure what to test, ask before proceeding.
- Target 80%+ coverage on the new code.
