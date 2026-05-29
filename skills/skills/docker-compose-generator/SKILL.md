---
name: docker-compose-generator
description: >
  Generates multi-stage Dockerfiles and docker-compose configurations optimized for size,
  security, and development workflow. Covers common stacks including Node.js, Python, Java, and Go.
  Triggers on: "create Dockerfile", "docker-compose", "containerize", "docker setup".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: devops
---

# Docker Compose Generator

## Instructions

### Step 1: Identify the Stack

Ask:
1. What language/runtime? (Node.js, Python, Java, Go, Ruby, .NET)
2. What framework? (Express, FastAPI, Spring Boot, Gin, Rails)
3. What services are needed? (database, cache, message queue, search)
4. Is this for development, production, or both?
5. Any existing Dockerfile to improve?

### Step 2: Generate Multi-Stage Dockerfile

Use multi-stage builds to minimize image size:

**Node.js example:**
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS production
RUN addgroup -g 1001 -S appgroup && \
    adduser -S appuser -u 1001 -G appgroup
WORKDIR /app
COPY --from=deps --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/package.json ./
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
CMD ["node", "dist/index.js"]
```

**Python example:**
```dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production
RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app
COPY --from=deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin
COPY --chown=appuser:appuser . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 3: Security Best Practices

Apply these rules to every Dockerfile:

1. **Non-root user** - always add a user and switch with `USER`
2. **Minimal base images** - prefer `-alpine` or `-slim` variants
3. **Pin versions** - use exact tags, never `latest`
4. **No secrets in image** - use build args or runtime env vars
5. **Read-only filesystem** - set `read_only: true` in compose where possible
6. **Drop capabilities** - add `cap_drop: [ALL]` in compose
7. **Health checks** - always include HEALTHCHECK instruction
8. **Scan for vulnerabilities** - add `docker scout cves` to CI

### Step 4: Generate docker-compose.yml

Create a compose file for the development environment:

```yaml
version: "3.8"

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      target: development
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgres://postgres:postgres@db:5432/appdb
      - REDIS_URL=redis://cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_started
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: appdb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 128mb --maxmemory-policy allkeys-lru

volumes:
  pgdata:
```

### Step 5: Production Compose Overlay

For production, provide a `docker-compose.prod.yml` overlay:

```yaml
version: "3.8"

services:
  app:
    build:
      target: production
    volumes: []
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
      restart_policy:
        condition: on-failure
        max_attempts: 3
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true

  db:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password

secrets:
  db_password:
    external: true
```

Usage: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up`

### Step 6: Common Service Snippets

Provide additional services as requested:

- **RabbitMQ:** `rabbitmq:3-management-alpine` with management UI on 15672
- **MongoDB:** `mongo:7` with init scripts in `/docker-entrypoint-initdb.d/`
- **Elasticsearch:** `elasticsearch:8.x` with single-node discovery
- **MinIO (S3-compatible):** `minio/minio` with console on 9001
- **Mailhog (dev email):** `mailhog/mailhog` with UI on 8025

## Example

User says: "Create a Docker setup for a Python FastAPI app with PostgreSQL and Redis"

Response:
- Multi-stage Dockerfile with slim base, non-root user, health check
- docker-compose.yml with app, postgres, redis services
- Volume mounts for hot reload in development
- Health check dependencies so app waits for DB
- .dockerignore file contents

## Guidelines

- Always use multi-stage builds for production images
- Never hardcode passwords in docker-compose files (use environment variables or secrets)
- Include .dockerignore in every project (exclude .git, node_modules, __pycache__, .env)
- Pin all image versions to specific tags
- Use health checks and depends_on with condition for startup ordering
- Default to Alpine-based images unless the app requires glibc
- Include resource limits in production configurations
- Provide both dev and prod configurations when asked for "Docker setup"
