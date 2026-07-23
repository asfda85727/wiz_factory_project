---
description: Design REST API endpoints for a feature
---

# API Design

Design REST API endpoints for: $ARGUMENTS

## Deliverables

1. **Endpoint list** — method, path, description, auth required (yes/no)
2. **Request/Response schemas** — with field names, types, required/optional, validation rules
3. **Error responses** — standard error format with HTTP status codes
4. **Data model** — what entities/collections/tables are needed

## Format

For each endpoint, provide:

```
[METHOD] /api/v1/resource
Auth: required / public
Request body: { ... }
Response 200: { ... }
Response 400: { error: "...", details: [...] }
```

## Guidelines
- RESTful naming: plural nouns for collections (`/users`, `/orders`), no verbs in paths.
- Use proper HTTP methods: GET (read), POST (create), PUT (full update), PATCH (partial update), DELETE.
- Use proper status codes: 200, 201, 204, 400, 401, 403, 404, 409, 422, 500.
- Pagination for list endpoints: `?page=1&size=20` or cursor-based.
- Filter and sort support where applicable.
- Consider rate limiting requirements.

## Rules
- DO NOT write code yet. This is design only.
- WAIT for approval before implementation.
- If the feature touches existing endpoints, read them first and stay consistent.
