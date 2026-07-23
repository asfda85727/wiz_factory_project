---
description: Review uncommitted code changes for quality and security
---

# Code Review

Review all uncommitted changes in this project.

## Process

1. Run `git diff` to see all staged and unstaged changes.
2. Run `git diff --cached` to see staged changes specifically.

## Check For

### Security
- [ ] Hardcoded secrets, API keys, passwords, tokens
- [ ] SQL injection (raw queries without parameterization)
- [ ] Missing input validation on user-facing endpoints
- [ ] Sensitive data in logs
- [ ] Missing auth/authorization checks

### Code Quality
- [ ] Functions longer than 50 lines
- [ ] Deep nesting (> 3 levels)
- [ ] Mutable shared state
- [ ] Missing error handling
- [ ] Copy-pasted / duplicated logic
- [ ] Dead code or unused imports

### Testing
- [ ] Are new code paths covered by tests?
- [ ] Are edge cases tested?

### Stack-Specific
- **Java**: proper use of Optional, records, @Transactional scope, resource cleanup
- **Python**: type hints present, async/sync consistency, Pydantic models for I/O
- **JS**: no `var`, no `any`, no `console.log`, proper error boundaries in React

## Output

Provide a summary with severity levels:
- **CRITICAL**: Must fix before merge (security, data loss)
- **WARNING**: Should fix (code quality, performance)
- **SUGGESTION**: Nice to have (style, readability)
