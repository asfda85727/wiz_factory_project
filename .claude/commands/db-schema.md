---
description: Design database schema for a feature
---

# Database Schema Design

Design the database schema for: $ARGUMENTS

## Process

1. **Identify entities** — what are the main objects and their relationships?
2. **Choose database** — PostgreSQL (relational, transactional) vs MongoDB (document, flexible) for each entity. Justify the choice.
3. **Design schema**:
   - PostgreSQL: tables, columns, types, constraints, indexes, foreign keys
   - MongoDB: collection structure, document shape, embedded vs referenced, indexes
4. **Plan migrations** — Flyway (Java) or Alembic (Python) migration files needed.

## Output Format

### For PostgreSQL
```sql
CREATE TABLE table_name (
    id          BIGSERIAL PRIMARY KEY,
    ...
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_table_column ON table_name(column);
```

### For MongoDB
```json
{
  "_id": "ObjectId",
  "field": "type",
  "embedded": { ... },
  "createdAt": "ISODate",
  "updatedAt": "ISODate"
}
```
With index definitions and schema validation rules.

## Guidelines
- Every table/collection gets `created_at` and `updated_at`.
- PostgreSQL: use `TIMESTAMPTZ`, `UUID` for public IDs, `BIGSERIAL` for internal PKs.
- MongoDB: embed data that's read together, reference data that's updated independently.
- Add indexes for every query pattern. Explain each index choice.
- Consider data growth — will this work at 10x/100x current scale?

## Rules
- DO NOT write application code yet. Schema design only.
- WAIT for approval before generating migration files.
