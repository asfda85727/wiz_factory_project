---
description: Incrementally fix build errors
---

# Fix Build Errors

## Process

1. Run the project's build command:
   - Java/Spring Boot: `./mvnw compile` or `./gradlew build`
   - Python: `mypy .` or `pyright`
   - JavaScript: `npm run build` or `npx tsc --noEmit`
2. Parse the FIRST error only.
3. Read the relevant file and fix that single error.
4. Re-run the build.
5. Repeat until build succeeds.

## Rules
- Fix ONE error at a time. Don't try to fix everything at once.
- If a fix introduces new errors, revert and try a different approach.
- After 5 consecutive failures on the same error, stop and explain the root cause.
- Don't suppress warnings with `@SuppressWarnings`, `# type: ignore`, or `// @ts-ignore` unless there's no alternative.
