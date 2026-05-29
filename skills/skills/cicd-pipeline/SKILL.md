---
name: cicd-pipeline
description: >
  Generates CI/CD pipeline configurations for GitHub Actions, GitLab CI, and AWS CodePipeline.
  Covers build, test, lint, security scanning, and deployment stages with caching and parallelism.
  Triggers on: "create CI/CD pipeline", "GitHub Actions workflow", "deployment pipeline", "automate build".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: devops
---

# CI/CD Pipeline

## Instructions

### Step 1: Gather Requirements

Ask:
1. What platform? (GitHub Actions, GitLab CI, AWS CodePipeline)
2. What language/framework? (Node.js, Python, Java, Go, .NET)
3. What stages are needed? (build, test, lint, security scan, deploy)
4. Deployment targets? (ECS, Lambda, Kubernetes, S3+CloudFront, Vercel)
5. Branch strategy? (deploy on main push, tag-based releases, environment promotion)

### Step 2: GitHub Actions Workflow

Generate a complete workflow file:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

permissions:
  contents: read
  id-token: write

env:
  NODE_VERSION: '20'
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm run lint
      - run: npm run type-check

  test:
    runs-on: ubuntu-latest
    needs: lint
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
      - run: npm ci
      - run: npm test -- --coverage
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/testdb
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - run: npm audit --audit-level=high
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
      - uses: github/codeql-action/analyze@v3

  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    if: github.ref == 'refs/heads/main'
    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    runs-on: ubuntu-latest
    needs: build
    environment: production
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-arn: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1
      - run: |
          aws ecs update-service \
            --cluster production \
            --service app \
            --force-new-deployment
```

### Step 3: Caching Strategies

Apply appropriate caching for the language:

**Node.js:**
```yaml
- uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'
```

**Python:**
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.12'
    cache: 'pip'
```

**Go:**
```yaml
- uses: actions/setup-go@v5
  with:
    go-version: '1.22'
    cache: true
```

**Docker layers:**
```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### Step 4: Parallelism and Job Dependencies

Structure jobs for maximum parallelism:

```
lint ──┬── test ──────┬── build ── deploy-staging ── deploy-prod
       │              │
       └── security ──┘
```

Rules:
- Lint and type-check first (fastest, catches most issues)
- Run tests and security scans in parallel (both depend on lint)
- Build only after tests and security pass
- Deploy with environment protection rules and manual approval for production

### Step 5: Environment Promotion

For multi-environment deployments:

```yaml
deploy-staging:
  needs: build
  environment: staging
  # Auto-deploys on main push

deploy-production:
  needs: deploy-staging
  environment:
    name: production
    url: https://app.example.com
  # Requires manual approval via GitHub environment protection rules
```

### Step 6: Deployment Target Configurations

**AWS ECS:**
```yaml
- uses: aws-actions/amazon-ecs-deploy-task-definition@v1
  with:
    task-definition: task-def.json
    service: my-service
    cluster: production
    wait-for-service-stability: true
```

**AWS Lambda:**
```yaml
- run: |
    zip -r function.zip .
    aws lambda update-function-code \
      --function-name my-function \
      --zip-file fileb://function.zip
```

**Kubernetes:**
```yaml
- uses: azure/k8s-set-context@v3
  with:
    kubeconfig: ${{ secrets.KUBE_CONFIG }}
- run: |
    kubectl set image deployment/app \
      app=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    kubectl rollout status deployment/app --timeout=300s
```

**S3 + CloudFront (static sites):**
```yaml
- run: |
    aws s3 sync dist/ s3://${{ vars.BUCKET_NAME }} --delete
    aws cloudfront create-invalidation \
      --distribution-id ${{ vars.CF_DISTRIBUTION_ID }} \
      --paths "/*"
```

## Example

User says: "Create a GitHub Actions pipeline for a Python FastAPI app deploying to AWS Lambda"

Response:
- Workflow with lint (ruff), test (pytest), security (pip-audit), build, deploy stages
- Python caching with pip
- AWS OIDC authentication (no long-lived keys)
- Lambda deployment with zip packaging
- Separate staging and production environments

## Guidelines

- Always use specific action versions (v4, not @main)
- Use OIDC for cloud provider authentication, never store long-lived credentials
- Run lint first because it is the fastest feedback
- Parallelize independent jobs (tests and security scans)
- Use GitHub environments with protection rules for production deployments
- Cache dependencies aggressively to reduce build times
- Set timeouts on all jobs to prevent hung workflows: `timeout-minutes: 15`
- Use `concurrency` groups to cancel outdated deployments
- Never expose secrets in logs; use `::add-mask::` if dynamic values are sensitive
