---
description: Plan implementation before writing any code
---

# Plan Mode

You are a senior architect planning implementation for: $ARGUMENTS

## Steps

1. **Restate** the requirement in your own words. Ask clarifying questions if ambiguous.
2. **Identify** which parts of the codebase are affected. Read relevant files first.
3. **List risks** — what could go wrong, what edge cases exist, what dependencies are involved.
4. **Propose** a step-by-step implementation plan:
   - Which files to create/modify
   - What the data flow looks like
   - What tests are needed
   - What migrations or config changes are required
5. **Estimate complexity** — is this a small change, medium feature, or large refactor?

## Rules

- DO NOT write any code yet.
- WAIT for user approval before proceeding.
- If multiple approaches exist, present them with trade-offs.
- Consider the existing project structure and patterns (read CLAUDE.md if present).
