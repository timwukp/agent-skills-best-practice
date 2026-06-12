# Reliability Pillar — Review Checklist

Engineering-level checks derived from the AWS Well-Architected Reliability Pillar.

## Foundations

- Service quotas checked against projected scale (common silent killers: EC2 vCPU quotas, EIP limits, Lambda concurrency, RDS connections); quota headroom monitored.
- Network topology has no single points: at least two AZs for anything production; NAT gateway per AZ (a single NAT gateway is an AZ-wide egress SPOF).

## Workload Architecture

- Stateless compute where possible; session/state externalized (ElastiCache, DynamoDB) so instances are replaceable.
- Multi-AZ on by default for production data stores: RDS Multi-AZ, Aurora with replica in second AZ, ElastiCache replication group. Single-AZ production database = High finding.
- Loose coupling at failure boundaries: queues (SQS) or streams between producers and consumers that can fail independently; synchronous chains of 3+ services flagged.
- Idempotency on retried operations (payment/order paths especially); retries with exponential backoff + jitter; circuit breakers on downstream calls.
- Timeouts explicitly set on every network call — the default-infinite-timeout chain is a classic cascading-failure source.

## Change Management

- Deployments are rollback-capable: blue/green, canary, or at minimum rolling with health checks gating progression. All-at-once production deploys = Medium+.
- Health checks validate real dependency health (shallow ping vs deep check trade-off considered); ALB/ASG health check grace periods sane.
- Auto scaling configured against the actual bottleneck metric, not just CPU; scale-in protected for stateful drains.

## Failure Management

- Backups: automated, encrypted, tested restores (an untested backup is a hope, not a control). RDS automated backups + snapshot retention aligned to RPO.
- DR posture matches stated RTO/RPO: backup-restore / pilot-light / warm-standby chosen deliberately and documented; cross-region replication where RTO demands it.
- Single-region production with no DR statement: ask for the RTO; if hours-not-days matters, flag Medium.
- Chaos/failure testing for critical paths (AZ failure simulation, dependency blackhole) — absence is Medium for high-criticality workloads.

## Common High-Severity Patterns

| Pattern | Why |
|---------|-----|
| Single-AZ production database | AZ event = full outage + possible data loss |
| No backups or untested restores | Unrecoverable data loss scenario |
| Synchronous call chain with no timeouts | One slow dependency cascades to total outage |
| Single NAT gateway for multi-AZ workload | Hidden cross-AZ SPOF |
| Quota ceiling within 2x of current usage | Scaling event hits an invisible wall |
