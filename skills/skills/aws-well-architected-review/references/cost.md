# Cost Optimization Pillar — Review Checklist

Engineering-level checks derived from the AWS Well-Architected Cost Optimization Pillar. Quantify findings where the artifact gives enough data.

## Visibility & Accountability

- Cost allocation tags on everything (environment, service, owner/team); untagged resources = unattributable spend. Tag policy enforced via IaC defaults.
- Budgets + anomaly detection (AWS Budgets, Cost Anomaly Detection) with alerts to owners, not a dead mailbox.

## Right-Sizing & Compute Economics

- Instance families current generation (m5→m7g class jumps are double-digit % cheaper-per-performance); Graviton considered for compatible workloads.
- Sizing justified by data, not copy-paste: flag anything that looks like "xlarge because the last one was xlarge". Compute Optimizer / utilization metrics referenced.
- Commitment coverage: steady-state baseline on Savings Plans/RIs; spiky/batch on Spot where interruption-tolerant (with diversification + capacity-rebalance); dev/test stopped out of hours (scheduler).
- Lambda memory tuned (memory = CPU; both over- and under-provisioning waste money); ARM where compatible.

## Storage Economics

- EBS: gp3 over gp2 (cheaper baseline + decoupled IOPS); orphaned volumes and aged snapshots lifecycle-managed.
- S3: lifecycle policies to IA/Glacier tiers for aging data, or Intelligent-Tiering when access patterns are unknown; incomplete multipart upload cleanup rule; versioning without lifecycle = unbounded growth.
- Logs: CloudWatch Logs retention set (never-expire default is a slow leak); high-volume logs considered for S3 + Athena instead of CloudWatch ingestion pricing.

## Data Transfer (the classic surprise)

- Cross-AZ traffic between chatty services flagged (per-GB both directions adds up); same-AZ affinity or VPC endpoints where appropriate.
- NAT gateway data processing for high-volume egress: S3/DynamoDB gateway endpoints are free and remove NAT per-GB charges.
- Cross-region replication and inter-region calls priced into the design, not discovered on the bill; CloudFront in front of high-egress endpoints.

## Architecture-Level Economics

- Serverless vs provisioned reasoned by load shape: always-on high-utilization → provisioned/containers; spiky/low-duty → Lambda/Fargate.
- Managed service premium vs ops cost articulated for the big-ticket choices (self-managed Kafka vs MSK, etc.).
- Multi-environment parity questioned: prod-sized staging running 24/7 is a finding.

## Common High-Severity Patterns

| Pattern | Typical impact |
|---------|----------------|
| No lifecycle on S3/logs/snapshots | Unbounded monotonic growth |
| Zero commitment coverage on steady 24/7 compute | ~30-40% overpay on baseline |
| High-volume egress through NAT gateway | Per-GB processing on traffic that could be free via endpoints |
| Prod-sized always-on non-prod environments | 2-3x environment multiplier on the bill |
| gp2 fleets at scale | ~20% storage overpay vs gp3 |
