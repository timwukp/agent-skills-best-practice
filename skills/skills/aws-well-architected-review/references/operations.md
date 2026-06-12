# Operational Excellence Pillar — Review Checklist

Engineering-level checks derived from the AWS Well-Architected Operational Excellence Pillar.

## Infrastructure as Code

- Everything in IaC (Terraform/CDK/CloudFormation); console-created production resources = drift and unreproducibility, flag them.
- State managed safely (Terraform: remote state + locking); IaC in CI with plan-review before apply; no apply-from-laptop for production.
- Environment parity through parameterization, not copy-paste stacks that drift apart.

## Observability

- Three signals present for each service: structured logs (with correlation/request IDs), metrics (RED: rate, errors, duration), traces across service boundaries (X-Ray/OTel) for multi-service flows.
- Alarms are symptom-based (user-facing latency, error rate, queue age) with runbook links — not just CPU thresholds; every alarm has an owner and an action, alarm fatigue is a finding.
- Dashboards exist for the golden paths; log retention deliberate (see cost pillar).

## Deployment & Change

- CI/CD pipeline with automated tests gating deploys; manual production deploys = Medium.
- Progressive deployment for user-facing services (canary/rolling with auto-rollback on alarm); database migrations decoupled from code deploys with rollback story.
- Feature flags for risky launches; deployment events annotated on dashboards (deploy markers).

## Operational Readiness

- Runbooks for the predictable: scaling events, failover, certificate rotation, dependency outage. A service with alarms but no runbooks pages people into improvisation.
- On-call reality: escalation path defined; post-incident reviews happen and produce backlog items (link to sprint-security-review skill's retro discipline where relevant).
- Game days / failure rehearsals for critical workloads; ops metrics reviewed (MTTR, change failure rate — DORA-style).

## Common High-Severity Patterns

| Pattern | Why |
|---------|-----|
| Console-managed production infrastructure | Unreproducible, undriftable, unauditable |
| No deploy rollback mechanism | Every bad deploy is a forward-fix fire drill |
| Alarms without runbooks or owners | Pages that train people to ignore pages |
| No correlation IDs across services | Multi-service debugging becomes archaeology |
| Database migrations coupled to app deploys | Rollback impossible at the worst moment |
