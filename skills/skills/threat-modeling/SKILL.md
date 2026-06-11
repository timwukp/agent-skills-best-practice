---
name: threat-modeling
description: >
  Performs STRIDE threat modeling for features, APIs, and architecture changes, producing a threat
  model document with risk-rated threats, mitigations, and security stories ready for the backlog.
  Use during sprint planning or design review. Triggers on: "threat model", "STRIDE", "security
  risks of this feature", "what could go wrong with this design", "security review of architecture".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: secure-sdlc
---

# Threat Modeling (STRIDE)

Produce a lightweight, sprint-compatible threat model: 15-30 minutes of structured analysis, not a multi-week security assessment. The output is a threat model document plus security stories the team can schedule.

## Process

1. **Establish the data flow.** Ask for (or derive from the code/design) the feature's data flow: actors, entry points, services, data stores, and trust boundaries. Summarize it as `Actor → Component → ... → Store`, marking each trust boundary crossing with `||`. If the user has architecture docs or code, read them instead of asking.
2. **Walk the STRIDE categories** against each trust boundary crossing (see table below). For each plausible threat, capture: description, category, likelihood (H/M/L), impact (H/M/L), and a concrete mitigation. Skip categories that genuinely don't apply — do not pad the table.
3. **Rate risk** as High if likelihood or impact is High and the other is at least Medium; Low only if both are Low; otherwise Medium.
4. **Generate security stories** for every High and Medium threat using the story format below (or hand off to the security-story-writing skill if it is available). Low threats go to the residual risk list with a one-line acceptance rationale.
5. **Deliver the document** using the template, and tell the user which stories should enter the next sprint.

## STRIDE Categories

| Category | Question to ask | Typical mitigations |
|----------|-----------------|---------------------|
| Spoofing | Can someone pretend to be a user, service, or device? | Strong authentication, mTLS, signed tokens |
| Tampering | Can data be modified in transit or at rest? | TLS, integrity checks, signed payloads, immutable logs |
| Repudiation | Can an actor deny performing an action? | Audit logging with identity + timestamp, log integrity |
| Information disclosure | Can data leak to the wrong party? | Encryption, least-privilege access, output filtering, masking |
| Denial of service | Can the component be made unavailable? | Rate limiting, quotas, timeouts, autoscaling, circuit breakers |
| Elevation of privilege | Can a user gain rights they shouldn't have? | AuthZ checks at every boundary, input validation, sandboxing |

## Threat Model Template

```markdown
# Threat Model: [Feature Name]
**Date:** [YYYY-MM-DD] · **Sprint/Milestone:** [if applicable] · **Participants:** [names/roles]

## Feature Description
[2-3 sentences: what it does and what data it touches]

## Data Flow
[User → Frontend || API Gateway → Service → Database]
(|| marks trust boundary crossings)

## STRIDE Analysis
| # | Threat | Category | Likelihood | Impact | Risk | Mitigation |
|---|--------|----------|-----------|--------|------|------------|
| 1 | [description] | [S/T/R/I/D/E] | H/M/L | H/M/L | H/M/L | [concrete control] |

## Security Stories Generated
- [ ] [Story title] — [priority] — [estimate if known]

## Residual Risks (accepted)
- [Low-risk threat] — [one-line justification for accepting]
```

## Security Story Format

```markdown
**As** [the system/security role], **I want** [security control], **so that** [risk is mitigated].
**Threat:** [STRIDE category + threat #] · **Source:** threat model [feature name]
**Acceptance:** Given [precondition], when [attack vector attempted], then [system prevents/detects/alerts].
```

## Guidelines

- Anchor every threat to a specific element of the data flow — "hackers could attack the API" is not a threat; "an unauthenticated caller can enumerate user IDs via GET /users/{id} (Information disclosure)" is.
- Prefer mitigations that already exist in the team's stack (their gateway, their IdP) over introducing new components.
- If the feature touches payment card data, personal data, or runs in a regulated industry, recommend a compliance pass (e.g. the fsi-compliance-checker skill for financial services) in addition to the threat model.
- For a brand-new system rather than a feature, model the 2-3 most critical flows first rather than attempting full coverage in one session.
