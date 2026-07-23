---
description: Generate Dockerfile and docker-compose for this project
---

# Docker Setup

Dockerize this project. Analyze the codebase first to detect the stack.

## Process

1. **Detect** the stack by reading build files (pom.xml, build.gradle, requirements.txt, package.json, go.mod).
2. **Generate Dockerfile** with:
   - Multi-stage build (build stage + runtime stage)
   - Specific base image tags (no `latest`)
   - Non-root user
   - Proper layer ordering for cache efficiency
   - Health check
3. **Generate docker-compose.yml** with:
   - App service
   - Database services (PostgreSQL, MongoDB, Redis) as detected
   - Kafka + Zookeeper if messaging is used
   - Proper volume mounts for data persistence
   - Network configuration
   - Environment variable placeholders
4. **Generate .dockerignore** excluding .git, build artifacts, node_modules, __pycache__, .env

## Stack-Specific Base Images
- Java 17: `eclipse-temurin:17-jdk-alpine` (build) + `eclipse-temurin:17-jre-alpine` (runtime)
- Python 3.12: `python:3.12-slim`
- Node.js: `node:20-alpine`

## Rules
- Don't expose unnecessary ports.
- Use environment variables for all config — no hardcoded values.
- Add comments explaining non-obvious choices.
