# Security Pillar — Review Checklist

Engineering-level checks derived from the AWS Well-Architected Security Pillar. Walk each area against the artifact; cite the specific resource in findings.

## Identity & Access (IAM)

- No wildcard actions/resources (`"Action": "*"`, `"Resource": "*"`) in roles attached to workloads; scope to the specific ARNs and actions used.
- Roles over users; no long-lived access keys in code, config, env files, or CI logs. Workloads assume roles (instance profiles, IRSA, task roles).
- Human access via identity federation/SSO with MFA; no shared accounts.
- Permission boundaries or SCPs constrain what CI/CD and provisioning roles can grant (privilege-escalation paths: `iam:PutRolePolicy`, `iam:PassRole` + compute-create).
- Cross-account access uses roles with external IDs, not credential sharing.

## Network Exposure

- Security groups: no `0.0.0.0/0` ingress except intentional public endpoints (and those are 80/443 behind ALB/CloudFront, not direct-to-instance SSH/RDP/DB ports).
- Databases, caches, and queues in private subnets; reachable only from their consumers' security groups (SG-references, not CIDR ranges).
- Public S3 access blocked at the account level unless a bucket is deliberately a public website; static content served via CloudFront with OAC, not public buckets.
- VPC endpoints for S3/DynamoDB/SSM traffic that shouldn't traverse the internet; egress control for sensitive workloads.

## Data Protection

- Encryption at rest on by default: EBS, RDS/Aurora, S3 (SSE-KMS for sensitive data with key policies, SSE-S3 acceptable for low-sensitivity), DynamoDB, SQS/SNS.
- TLS in transit everywhere external and between services where feasible; no plaintext listener ports; cert validation not disabled anywhere.
- KMS: customer-managed keys for sensitive data with rotation enabled; key policy doesn't grant `kms:*` broadly; secrets in Secrets Manager/SSM Parameter Store (SecureString), never in env-var plaintext in task definitions or user data.
- Backups/snapshots inherit encryption; snapshot sharing is not public.

## Detection & Response

- CloudTrail on (all regions, log file validation); GuardDuty enabled; findings routed to a human-visible destination.
- Security-relevant application events logged (authn/authz failures, privilege changes) and alarmed.
- An incident response path exists: isolating a compromised resource (SG quarantine, credential revocation) is documented and feasible.

## Application Security

- Public-facing endpoints behind WAF (managed rule sets at minimum) where they handle authentication or user data.
- Input validation at service boundaries; dependencies scanned (ECR scanning, dependency scanning in CI).
- Compute runs least-privilege: containers non-root, no privileged mode without justification; Lambda functions don't share one mega-role.

## Common High-Severity Patterns

| Pattern | Why it stops the meeting |
|---------|--------------------------|
| Public S3 bucket with non-public data | Breach-by-default |
| `*:*` IAM on a workload role | One bug = account takeover |
| Database port open to 0.0.0.0/0 | Internet-scannable data store |
| Secrets in plaintext env/user-data/repo | Credential leak with rotation pain |
| No CloudTrail / single-region trail | Blind during incident response |
