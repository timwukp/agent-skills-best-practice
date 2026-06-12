# Sustainability Pillar — Review Checklist

Engineering-level checks derived from the AWS Well-Architected Sustainability Pillar. Most sustainability wins are also cost wins; cite both when true.

## Utilization (the core lever)

- Right-size aggressively: sustained low utilization (<20% CPU/memory) is wasted carbon and money; consolidate or downsize.
- Scale-to-zero where the workload allows: dev/test off out of hours, Lambda/Fargate for spiky loads, scheduled scaling for predictable troughs.
- Batch and async work scheduled into fewer, fuller compute units rather than always-on idle capacity.

## Hardware & Region Efficiency

- Current-generation instances (better performance-per-watt every generation); Graviton/ARM where compatible — meaningful efficiency-per-watt gain.
- Managed/serverless services preferred where fit: shared AWS infrastructure runs at higher utilization than dedicated under-used clusters.
- Region selection: where latency/residency allows choice, prefer regions with lower-carbon energy profiles; note when data residency (e.g. FSI requirements) fixes the region — that's a constraint, not a finding.

## Data Lifecycle

- Data has an expiry plan: lifecycle policies to colder tiers and deletion; "keep everything forever" is a sustainability and cost finding.
- Compression on stored and transferred data where cheap (logs, exports, Parquet over CSV for analytics).
- Redundant copies deliberate, not accidental (orphaned snapshots, forgotten replicas, debug copies of production datasets).

## Development Practice

- Build/CI efficiency: cached builds, right-sized runners, no always-on idle build fleets.
- Test environments ephemeral where possible (create-test-destroy) rather than long-lived parallel estates.

## Common Findings

| Pattern | Note |
|---------|------|
| 24/7 dev/test environments | Scheduler = ~70% reduction on those resources |
| Previous-generation instance fleets | Free efficiency upgrade left unclaimed |
| No data lifecycle anywhere | Monotonic storage growth, carbon and bill |
| Idle over-provisioned "headroom" fleets | Auto scaling exists to make this unnecessary |
