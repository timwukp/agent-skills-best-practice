# Performance Efficiency Pillar — Review Checklist

Engineering-level checks derived from the AWS Well-Architected Performance Efficiency Pillar.

## Selection

- Compute type matches the workload: CPU-bound → compute-optimized; memory-heavy caches/analytics → memory-optimized; bursty low-duty → burstable (with CPU-credit exhaustion understood) or Lambda.
- Database engine matches access pattern: relational for transactions/joins; DynamoDB for known-key high-scale access; ElastiCache in front of read-heavy hot paths; OpenSearch for search — flag relational databases doing full-text search or key-value-only duty at scale.
- Storage matches I/O: gp3 baseline, io2 only with evidenced IOPS need; instance store for ephemeral scratch; EFS vs EBS vs S3 chosen by access semantics, not familiarity.

## Caching & Data Path

- A defined caching strategy for read-heavy paths: CloudFront for static/cacheable edge content, ElastiCache/DAX for hot data, TTLs and invalidation reasoned (cache without invalidation strategy = future incident).
- N+1 query patterns and chatty service-to-service loops flagged; batch APIs used where offered (DynamoDB BatchGet, SQS batch).
- Connection pooling for RDS from Lambda/high-concurrency compute (RDS Proxy where connection storms are plausible).
- Pagination on unbounded queries; no SELECT * over wide tables on hot paths.

## Scaling Behavior

- Scaling metric matches the real bottleneck (queue depth, p99 latency, connections — not CPU-by-default).
- Pre-warming/scheduled scaling for known traffic patterns; Lambda provisioned concurrency where cold starts breach latency SLOs.
- Async where the user doesn't need to wait: long work behind queues with status polling/webhooks, not 30-second synchronous requests.

## Measurement (no data, no performance claims)

- Latency SLOs stated (p50/p99) for user-facing paths; load testing exists for launch-critical paths.
- Observability covers the data path: slow-query logs, X-Ray/tracing on cross-service flows, RED metrics per service.
- "We'll optimize later" is fine; "we can't see it" is a finding.

## Common High-Severity Patterns

| Pattern | Why |
|---------|-----|
| Burstable instances on sustained-load production | CPU credit exhaustion = mystery brownouts |
| Lambda → RDS without pooling/proxy at scale | Connection storms take down the database |
| Hot path with zero caching and known read skew | Paying full compute for repeated identical work |
| Synchronous user requests doing batch-scale work | Timeouts, retries, duplicate side effects |
| No p99 visibility on user-facing latency | Averages hide the experience users actually have |
