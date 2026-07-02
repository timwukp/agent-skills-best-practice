# Validation Report: Kiro CLI on a Closed VPC (AWS PrivateLink Only)

**Test date**: 2026-07-02
**Test environment**: disposable AWS test account (not a customer account), us-east-1
**Subject under test**: kiro-cli 2.10.0
**Report status**: all core items validated; all test resources deleted and verified gone
**Referenced from**: `skills/skills/gitlab-ci-kiro-pipeline/references/kiro-cli-headless.md` ("Air-gapped runners" section)

---

## 1. Purpose

Validate the following enterprise deployment pattern:

> A GitLab Runner sits in a private VPC with **no outbound internet access at
> all** (no Internet Gateway, no NAT Gateway), reaching the Kiro/Q Developer API
> exclusively through an **AWS PrivateLink Interface VPC Endpoint**, with the
> `kiro-cli` binary **staged manually** rather than installed via
> `curl | bash` from the public internet. Does the full
> install → authenticate → chat flow work end to end?

This matches network architectures common in regulated industries (finance,
government, and other high-security environments).

## 2. Method

The approach was "form a hypothesis, then verify it in a real environment" —
not simply trusting inference from documentation. Steps:

1. Create a brand-new, fully isolated VPC in a test AWS account with no route to
   the internet.
2. Create an AWS PrivateLink Interface VPC Endpoint
   (`com.amazonaws.us-east-1.q`) with Private DNS enabled.
3. Launch an EC2 instance with **no public IP** in a private subnet of that VPC,
   simulating a GitLab Runner sandbox.
4. Run **control-group tests** to confirm the environment is genuinely isolated
   (connections to public sites should fail; domains covered by PrivateLink
   should resolve to private IPs).
5. Use an **S3 Gateway Endpoint** to stand in for an enterprise's internal
   artifact store: download the binary ahead of time on a machine with internet
   access, verify its checksum, upload it, then pull it from inside the isolated
   environment.
6. Run `kiro-cli chat --no-interactive` with a real headless API key to complete
   an end-to-end conversation test.
7. Cross-verify with a **raw network-layer test** (TCP + TLS handshake) that
   bypasses the CLI entirely, so the conclusion doesn't rest on application-layer
   behavior alone.
8. Delete every test resource after the test and confirm deletion.

## 3. Environment design

### 3.1 Network topology

```
+-------------------------------------------------------------+
| Isolated test VPC (10.99.0.0/16)                             |
| Route table: local route only, no 0.0.0.0/0, no IGW           |
|                                                               |
|  +---------------------------------------------------------+ |
|  | Private subnet (10.99.1.0/24)                           | |
|  | MapPublicIpOnLaunch = false                              | |
|  |                                                           | |
|  |  +----------------------+                                | |
|  |  | Test EC2 instance    |  <- simulates GitLab Runner     | |
|  |  | (no public IP)       |     sandbox                     | |
|  |  +----------------------+                                | |
|  +---------------------------------------------------------+ |
|                                                               |
|  Interface VPC Endpoints:                                    |
|  +- com.amazonaws.us-east-1.q       <- SUBJECT UNDER TEST     |
|  |                                     (API access path)      |
|  +- com.amazonaws.us-east-1.ssm            -+                 |
|  +- com.amazonaws.us-east-1.ssmmessages     |<- operator       |
|  +- com.amazonaws.us-east-1.ec2messages    -+  management path |
|                                              (not under test)  |
|                                                               |
|  Gateway VPC Endpoint:                                        |
|  +- com.amazonaws.us-east-1.s3      <- stands in for the      |
|                                        customer's internal    |
|                                        artifact store          |
+-------------------------------------------------------------+
                              |
                     (no route whatsoever)
                              |
                              x
                  Public internet / cli.kiro.dev
```

### 3.2 Key design decisions

- **Subject under test vs. operator channel**: the `q` PrivateLink endpoint is
  the only thing this test set out to validate. The three SSM endpoints exist
  purely so the test operator could manage the instance remotely — a real
  GitLab Runner does not need them, and they were not counted as part of the
  pattern being validated.
- **S3 Gateway Endpoint as the internal artifact store stand-in**: mirrors the
  real-world pattern of "download the binary once where there's internet, then
  serve it internally via S3 / Artifactory / Nexus / GitLab Package Registry."
  Gateway Endpoints are free and require no extra infrastructure — AWS's
  standard recommendation for private S3 access.
- **Control-group methodology**: on the same instance, domains covered by
  PrivateLink and domains that are not were tested side by side, so the
  conclusion rests on a behavioral contrast (DNS resolution + connection
  outcome) rather than a single isolated result.

## 4. Results

### 4.1 Environment isolation (control group)

| Test | Result | Notes |
|---|---|---|
| `curl https://www.google.com` | Timed out | Confirms no route to the public internet |
| DNS resolution of `cli.kiro.dev` | Succeeded, returned public IPs (CloudFront, e.g. 13.226.209.x) | DNS works fine; these are public IPs |
| `curl https://cli.kiro.dev/install` | Connection failed | Because those public IPs are unreachable from this VPC — confirms this domain is NOT covered by PrivateLink |
| DNS resolution of `q.us-east-1.amazonaws.com` | Succeeded, returned a private IP inside the VPC CIDR (the PrivateLink endpoint's ENI) | Confirms Private DNS override is active and the API domain is routed privately |

**Conclusion**: the environment design is correct — a clean, trustworthy
simulation of a closed network.

### 4.2 Manual binary staging

| Step | Result |
|---|---|
| Download `kirocli-x86_64-linux.tar.gz` (2.10.0) on an internet-connected machine | Succeeded, 552,142,249 bytes |
| SHA-256 checksum vs. official `manifest.json` | Exact match |
| Upload to the stand-in "internal artifact store" S3 bucket | Succeeded |
| Download from the isolated EC2 (no internet) via the S3 Gateway Endpoint only | Succeeded, ~80–110 MiB/s |
| Re-verify checksum after transfer | Exact match again — confirms lossless transfer |
| Extract, run bundled installer, `kiro-cli --version` | Succeeded, reported `kiro-cli 2.10.0` |

**Conclusion**: the "download once, verify, stage internally" pattern is fully
workable and lets an enterprise control exactly which version and binary
integrity it deploys.

### 4.3 PrivateLink network layer (bypassing the CLI)

On the isolated instance, without going through `kiro-cli` at all, a raw
connection test was made directly to `q.us-east-1.amazonaws.com:443`:

| Test | Result |
|---|---|
| TCP connect (`/dev/tcp`) | Succeeded |
| TLS handshake (`openssl s_client`) | Succeeded, full certificate chain verified |
| Server certificate subject | `CN=*.codewhisperer.us-east-1.vpce.amazonaws.com` |

**Conclusion**: this is the decisive technical evidence — the certificate
subject explicitly identifies the PrivateLink endpoint as the TLS termination
point, proving the connection genuinely traverses the private network path
rather than some unexpected route or cached result.

### 4.4 End-to-end headless authentication and chat

An initial test without an API key failed with "Failed to open browser for
authentication." Checking the official documentation
([kiro.dev/docs/cli/headless](https://kiro.dev/docs/cli/headless/)) confirmed
that headless mode requires the `KIRO_API_KEY` environment variable — an
officially supported authentication method (requiring a Pro/Pro+/Pro
Max/Power subscription, with an administrator having enabled API key
generation in the Kiro console).

Re-running with the key set:

```bash
export KIRO_API_KEY=<valid test key>
kiro-cli chat --no-interactive --trust-tools=read "<prompt>"
```

| Item | Result |
|---|---|
| Exit code | 0 |
| Response | A genuine model reply (not an error message) |
| Credits/time shown | `Credits: 0.02 - Time: 2s` |

A non-zero credits value confirms this was a real request that reached the
backend and consumed a metered resource — not a local cache or offline
simulation.

**Conclusion**: "PrivateLink API access + manually staged binary +
`KIRO_API_KEY` headless authentication," combined, works end to end in an
environment with zero outbound internet access.

### 4.5 Secret handling

The test API key was supplied directly by the person running this validation,
with a stated 30-minute expiry, and expired shortly after the test. A
post-test check confirmed no trace of the key was left in the instance's home
directory; the only place it appeared was the SSM agent's own operational log
(standard SSM behavior for any command it executes), which was destroyed along
with the rest of the test VPC/EC2 during cleanup.

## 5. Resource cleanup confirmation

All test resources were deleted and re-verified:

| Resource | Status |
|---|---|
| EC2 instance | Terminated (confirmed via `wait instance-terminated`) |
| 5 VPC Endpoints (q, ssm, ssmmessages, ec2messages, S3 gateway) | All deleted, confirmed gone via `describe-vpc-endpoints` |
| S3 bucket | Emptied and deleted, `head-bucket` returns 404 |
| Security group | Deleted |
| Subnet | Deleted |
| VPC | Deleted, `describe-vpcs` returns `InvalidVpcID.NotFound` |

Zero residual resources confirmed.

## 6. Summary for enterprise customers

1. **API access**: create an Interface VPC Endpoint
   (`com.amazonaws.<region>.q`) with Private DNS enabled. `kiro-cli chat` then
   runs entirely over the private network with no additional configuration.
2. **CLI install**: the official `curl | bash` installer cannot reach the
   internet in this topology. Enterprises should instead:
   - Download `manifest.json` and the binary for their platform on a machine
     with internet access, verifying the SHA-256 checksum from the manifest.
   - Upload the verified binary to an internal artifact store (S3 + a Gateway
     Endpoint is the simplest option).
   - Change the GitLab CI install step to pull from the internal path instead
     of the public internet.
   - Set up a periodic sync process so the internal copy doesn't drift from
     the latest release.
3. **Authentication**: use the `KIRO_API_KEY` environment variable (as a
   masked GitLab CI/CD variable) — this is the officially supported headless
   authentication method. It requires:
   - A Kiro Pro / Pro+ / Pro Max / Power subscription.
   - An administrator enabling "Enable users to generate API keys" in the
     Kiro console.
   - The user generating their own API key from the Kiro portal.
4. **Scope of this test**: this validation used a short-lived personal test
   key in a disposable test account, not a customer's production environment.
   Customers should still run their own pipeline test after wiring this up in
   their real GitLab environment, confirming that their organization's
   governance settings (model restrictions, MCP restrictions, etc.) behave as
   expected under headless mode. MCP server behavior and multi-job pipeline
   mechanics were not re-tested in this air-gapped topology — they are
   unaffected by the network path and are already covered by the rest of this
   skill's guidance, but customers with an MCP-dependent pipeline should still
   verify that specifically.
