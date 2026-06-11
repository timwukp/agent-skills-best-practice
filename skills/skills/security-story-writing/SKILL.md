---
name: security-story-writing
description: >
  Writes security user stories and security-aware acceptance criteria that fit a Scrum backlog,
  converting threats, scan findings, and compliance requirements into INVEST-compliant stories with
  Given/When/Then criteria and regression tests. Use this (not general story writing) whenever the
  story or criteria concern a security control, vulnerability, or compliance requirement. Triggers
  on: "write a security story", "security acceptance criteria", "acceptance criteria for rate
  limiting/auth/validation", "Given/When/Then for this security control", "turn this vulnerability
  into a backlog item", "convert these scan findings to stories".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: secure-sdlc
---

# Security Story Writing

Convert security work — threats from a threat model, SAST/DAST findings, pen-test results, compliance controls — into stories a Scrum team can estimate, schedule, and verify like any other backlog item.

## Story Types

Pick the right shape for the input:

1. **Security control story** — a new protective capability (rate limiting, input validation, audit logging). Written from the system's or security role's perspective.
2. **Vulnerability remediation story** — fixing a specific finding. Must reference the finding ID and include a regression test criterion.
3. **Feature story with security criteria** — a normal feature story that gains explicit security acceptance criteria. Use when security is a property of the feature, not separate work.
4. **Compliance story** — implementing a named control from a framework (PCI-DSS requirement, MAS TRM section). Must cite the specific control number so auditors can trace it.

## Templates

### Security control story
```markdown
### [ID] [Control title]
**As** [the system / a security role], **I want** [security control], **so that** [risk is mitigated].
**Threat:** [STRIDE category or threat-model reference]
**Compliance:** [framework + control number, if applicable]

#### Acceptance Criteria
- Given [precondition], when [attack vector attempted], then [system prevents/detects and logs/alerts]
- Given [precondition], when [normal operation], then [control is active without breaking the user flow]

#### Security Regression Test
- Automated test proving [the attack] fails, runs in CI from this sprint onward
```

### Vulnerability remediation story
```markdown
### [ID] Fix: [finding title]
**Finding:** [scanner/report ID, severity, CVSS if available]
**Affected:** [component, endpoint, or file]

#### Acceptance Criteria
- Given the conditions in the finding, when [the exploit is attempted], then it fails
- The fix introduces no functional regression in [affected flows]
- A regression test reproducing the original exploit is added to CI
```

### Feature story with security criteria
```markdown
### [ID] [Feature title]
**As a** [user], **I want to** [action], **so that** [business value].
**Security consideration:** [what could go wrong — one line, STRIDE reference if a threat model exists]

#### Acceptance Criteria
- [Functional criteria as usual]
- **Security:** [the specific security property, testable — e.g. "responses never include other users' data, verified by an authorization test"]
```

## Quality Bar (apply before delivering)

- **Testable**: every criterion can be verified by a test or demonstrated in review. "Is secure" fails this bar; "locks the account after 5 consecutive failed logins within 15 minutes" passes.
- **INVEST-compliant**: independently schedulable, estimable, sized for one sprint. Split stories that bundle multiple controls.
- **Traceable**: remediation stories cite the finding; compliance stories cite the control number; threat-derived stories cite the threat model entry.
- **Negative path included**: at least one criterion describes what happens when the attack is attempted, not only the happy path.

## Examples

- "As the authentication service, I want to lock accounts after 5 consecutive failed login attempts within 15 minutes, so that brute-force attacks are prevented." (control story; criteria cover the lockout, the unlock path, and the audit log entry)
- "As the transfer API, I want all amount and account inputs validated server-side against strict schemas, so that injection and tampering attempts are rejected." (control story derived from a Tampering threat)

## Guidelines

- Severity drives priority: Critical/High vulnerabilities are P0/P1 and should not wait for "a security sprint" — recommend they enter the current sprint.
- When converting a batch of scan findings, group by root cause (e.g. one story for "parameterize all queries in module X", not 14 stories for 14 query sites).
- Don't write security theater: if a requested control doesn't mitigate a real threat for this system, say so and propose what actually would.
