# Enterprise roadmap

Six gaps in this skill's enterprise story **are** self-addressable — unlike the three
controls in `references/enterprise-adoption.md`, which require authority this repository
cannot hold. This file orders that work and states what evidence would close each item.

**Status of everything here: `proposed`.** This is **not an SLA**, not a delivery date, and
carries **no funded** commitment or assigned owner. Nothing below has been accepted for
delivery. Each workstream must begin with its own **accepted intent** under the slug given,
reviewed and approved by a human, and ship as its own pull request. Bundling them would
defeat review: their dependencies, owners and evidence horizons differ by an order of
magnitude.

None of this work raises the readiness score by itself. Evidence does that, and for the
last two workstreams the evidence includes elapsed time that cannot be compressed.

## Portfolio

| Phase | Workstream | Slug | Depends on |
|---|---|---|---|
| 0 | Operational ownership | `operational-ownership` | — |
| 0 | Enterprise telemetry contract | `enterprise-telemetry` | — |
| 1 | Schema migration and fleet inventory | `schema-migration-fleet-inventory` | telemetry (for fleet state) |
| 1 | Stage 6 feedback loop | `stage6-feedback-loop` | telemetry (deterministic signals) |
| 2 | Production-scale evidence | `production-scale-evidence` | fleet inventory, ownership |
| 3 | Longitudinal operational evidence | `longitudinal-operational-evidence` | telemetry, ownership, elapsed real time |

Phases order dependencies, not calendar time. Separately approved work may proceed in
parallel wherever its dependencies are already satisfied.

- **Phase 0 — ownership and measurement.** Nothing later can be evidenced without knowing
  who is responsible and without a way to measure what happens.
- **Phase 1 — lifecycle and fleet state.** Make the deployed population observable and
  upgradable, and close the loop from production signal back into a new intent.
- **Phase 2 — representative scale evidence.** Replace synthetic fixtures with consenting
  real repositories.
- **Phase 3 — longitudinal evidence.** Report what actually happened over a declared
  observation window.

---

### Workstream 1 — Operational ownership

- **Problem:** the project publishes a disclosure channel but no maintenance commitment.
  An enterprise cannot depend on a control whose response behaviour is unstated.
- **Enterprise value:** makes dependency risk assessable — an adopter can decide whether
  the response profile is acceptable instead of guessing at it.
- **Depends on:** nothing.
- **Bounded deliverable:** a written ownership record — named maintainer roles, security
  triage target, escalation path, decision rights for enforcement-generation changes, and
  an explicit statement of what is best-effort.
- **Verification target:** a test asserting the ownership record exists, names roles rather
  than individuals' availability, and states its own limits; plus a dated response-time
  record for real reported issues.
- **Exit evidence:** the ownership document, and at least one observation window of actual
  response times against the stated target.
- **Non-goals:** an SLA, a funded on-call rotation, a legal support obligation, or any
  promise of response time this project cannot keep.
- **Follow-up intent slug:** `operational-ownership`
- **Status:** proposed

### Workstream 2 — Enterprise telemetry contract

- **Problem:** adoption, block and bypass rates are invisible. Gap 4 in
  `references/limitations.md` has been open since the beginning, and every later evidence
  claim depends on it.
- **Enterprise value:** turns "the gate is installed" into "the gate stopped N ungoverned
  changes and produced M false positives".
- **Depends on:** nothing.
- **Bounded deliverable:** a privacy-bounded event schema and a local emitter — event
  names, field types, an explicit no-content rule (no diffs, no file contents, no user
  identifiers), an opt-in transmission boundary, and a documented baseline metric set.
- **Verification target:** a test asserting the schema forbids content and identity fields,
  that emission is off unless explicitly enabled, and that the emitter never blocks or
  fails the gate.
- **Exit evidence:** the schema, the emitter with tests, and a baseline metric report from
  at least this repository.
- **Non-goals:** transmitting repository or user data anywhere by default, a hosted
  collector, or any telemetry that changes gate outcomes.
- **Follow-up intent slug:** `enterprise-telemetry`
- **Status:** proposed

### Workstream 3 — Schema migration and fleet inventory

- **Problem:** `.sdlc/version` exists, but migration tooling does not, and there is no way
  to see which version or configuration each consuming repository actually runs.
- **Enterprise value:** makes an upgrade a planned rollout with drift visibility instead of
  a coordinated surprise, and lets a policy owner answer "what is deployed" by query.
- **Depends on:** `enterprise-telemetry` for fleet state reporting.
- **Bounded deliverable:** a migration command that upgrades artifacts between schema
  versions with a dry-run mode and refuses ambiguous cases, plus an inventory report of
  gate version, schema version and enforcement configuration per repository.
- **Verification target:** round-trip migration tests across every supported schema
  version, a test that a partially migrated chain is refused rather than half-upgraded, and
  an inventory test against fixture repositories.
- **Exit evidence:** the migration tool with tests, and an inventory report covering more
  than one real consuming repository.
- **Non-goals:** a hosted fleet service, automatic upgrades without adopter consent, or
  silent rewriting of accepted artifacts.
- **Follow-up intent slug:** `schema-migration-fleet-inventory`
- **Status:** proposed

### Workstream 4 — Stage 6 feedback loop

- **Problem:** Stage 6 is documented but does not close. A production signal does not become
  a new `intent.md`, so the lifecycle is a line rather than a loop.
- **Enterprise value:** incidents re-enter the governed process instead of being fixed
  outside it, which is where ungoverned change actually originates.
- **Depends on:** `enterprise-telemetry` for deterministic signals.
- **Bounded deliverable:** a deterministic path from a declared band breach to a drafted
  intent — threshold evaluation, an idempotent draft with provenance back to the signal,
  and a required human acceptance step before any stage advances.
- **Verification target:** tests proving a breach drafts exactly one intent, that repeated
  breaches do not multiply drafts, that the draft cannot self-accept, and that no model
  output sits in the detection path.
- **Exit evidence:** the implemented path with tests, and one real incident carried from
  signal to accepted intent.
- **Non-goals:** placing a model in the detection path, auto-accepting generated intents,
  or acting on a signal without a human decision.
- **Follow-up intent slug:** `stage6-feedback-loop`
- **Status:** proposed

### Workstream 5 — Production-scale evidence

- **Problem:** the scale, monorepo, polyglot and concurrency coverage in CI is synthetic —
  fixtures this project built to exercise its own code paths. The largest real exercise is
  a few dozen files, and live fork-token semantics remain unproven.
- **Enterprise value:** an adopter with a large repository can see whether the gate holds at
  their shape, rather than extrapolating from a fixture.
- **Depends on:** `schema-migration-fleet-inventory` and `operational-ownership`.
- **Bounded deliverable:** reproducible exercises against consenting external or bounded
  real repositories across monorepo, polyglot, fork-based contribution, concurrent pull
  request and multi-platform scenarios, with recorded timings, failures and a redaction
  procedure.
- **Verification target:** a published result set per scenario with the commit and
  repository shape recorded, plus refreshed support-matrix entries that distinguish
  synthetic from real coverage.
- **Exit evidence:** the result set, the reproduction procedure, and defects found and
  fixed as a consequence.
- **Non-goals:** presenting synthetic fixtures as production adoption, publishing adopter
  code or identities without consent, or claiming a scenario passed without recorded output.
- **Follow-up intent slug:** `production-scale-evidence`
- **Status:** proposed

### Workstream 6 — Longitudinal operational evidence

- **Problem:** there is no record of how this control behaves over time — no adoption curve,
  no false-positive rate, no bypass frequency, no incident and recovery history.
- **Enterprise value:** this is the evidence a risk owner actually asks for, because a
  control that works on day one and is bypassed by month three is not a control.
- **Depends on:** `enterprise-telemetry`, `operational-ownership`, and **elapsed** real
  time in production use.
- **Bounded deliverable:** a reporting procedure and a first report over a declared
  observation window — adoption, block rate, false-positive rate, bypass frequency,
  incidents, recovery times, and the deployed version distribution.
- **Verification target:** a test asserting the report declares its observation window and
  its data source, and refuses to render a window that has not actually elapsed.
- **Exit evidence:** at least one completed observation window of real operational data,
  with the window's start and end dates recorded.
- **Non-goals:** synthesising a window from fixtures, extrapolating from a single
  repository, or reporting a period longer than the data covers. **This workstream cannot
  be closed by a synthetic test run**: time is the input, and no test can manufacture it.
- **Follow-up intent slug:** `longitudinal-operational-evidence`
- **Status:** proposed

---

## What completing all six would and would not achieve

It would close Gaps 4, 5, 8 and 10 in `references/limitations.md` and supply the evidence
base that the enterprise-wide position requires. It would **not** close the three controls
in `references/enterprise-adoption.md`, because policy authority, external evidence custody
and independence are not ours to grant. The regulated position additionally needs assurance
under the applicable framework.

The readiness score stays at 36/80 until controls and evidence change. Adding this roadmap
changed nothing about what is deployed.
