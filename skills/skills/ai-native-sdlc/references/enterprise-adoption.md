# Enterprise adoption contracts

Three of the controls an enterprise needs from a governance tool **cannot be delivered by
this repository at all**, no matter how much code is written here. They require authority,
evidence custody and independence that a skill installed inside the governed repository
does not have and must not claim to have.

This document is the integration boundary. For each of those three controls it states what
outcome the enterprise must achieve, what evidence proves it, and how to test that the
evidence is real — without prescribing a vendor.

**What this repository supplies:** a stage gate that fails closed, a machine-readable
artifact format, a mutation-verified test suite, signed releases with an SBOM and
provenance, and a documented verification procedure.

**What the adopting enterprise must supply:** policy authority above the repository,
custody of evidence outside the governed party, verified organisational identity, and an
independent assessment. Those four are the subject of this document.

**Examples here are illustrative.** Named products appear only to make a contract concrete.
Equivalent controls from any other vendor, or built in-house, satisfy the contract equally.
Copying a sample configuration **does not prove** the control works; only the retained
evidence and the negative controls in each section do.

---

## Control 1 — Organisation policy plane

### Owner and boundary

**Owner:** the platform or developer-experience function that administers the source
forge at organisation or enterprise level, together with the identity function that owns
account lifecycle.

This control is **enterprise-owned**. The boundary is the repository wall: everything
inside a repository can be edited by someone with administrative rights to that
repository, so a control that lives inside it can always be removed by the party it
governs. Policy authority must therefore sit at a tier the governed engineer cannot reach.
The gate in this repository is the thing being *mandated*; it is never the thing doing the
mandating.

### Minimum required properties

1. **Centrally managed.** One policy change takes effect across every in-scope repository
   without per-repository work, and its state is readable centrally.
2. **Repository administrators cannot weaken it.** A repository admin may add stricter
   rules and may never relax the central baseline. If the deployment has no tier above the
   repository owner — a personal account, for example — this property is unachievable
   there and the tier must be recorded as unmet rather than approximated.
3. **Owned exception path.** Bypass is a named, time-bounded, logged grant held by a role
   distinct from the engineer requesting it. An unlimited standing exception is a disabled
   control with extra paperwork.
4. **Verified identity.** Commit and approval actors resolve to accounts governed by the
   enterprise directory, with the verification signal recorded. Otherwise "who approved
   this" is a display name that anyone can type.
5. **Required checks always report.** A policy that requires a check which can be skipped
   is advisory: a skipped check is not a passing check, and a check that never reports
   blocks the pull request forever instead of governing it.
6. **Fleet-visible state.** The deployed policy version and its per-repository
   configuration are enumerable, so drift is a query rather than an audit interview.

### Acceptance contract

The control is accepted when, for a declared scope of repositories, the enterprise can
demonstrate all of the following without editing anything inside the governed repository:

- a change to central policy is observed to take effect in a repository whose
  administrators did not act;
- an attempt by a repository administrator to weaken the baseline is refused, with the
  refusal recorded;
- every exception in force is enumerable with grantee, grantor, reason and expiry;
- the required-check list is enforced and each entry reports a real conclusion; and
- the current policy version is reported for every repository in scope.

### Reference architecture (non-normative)

One implementation that satisfies the contract on GitHub: an **organisation- or
enterprise-level ruleset** whose bypass list excludes repository administrators, requiring
the `sdlc-gate` and `gate tests green` checks, combined with SAML/SCIM-governed accounts
and required commit signing. Exceptions are granted as time-bounded bypass entries owned
by the platform team. Equivalent controls on another forge, or an admission controller in
front of the forge, are equally valid.

### Evidence package

Retain: the policy definition under version control; the bypass roster with expiry dates;
a dated export of per-repository policy state for the declared scope; the refusal record
from the weaken attempt; and the identity-verification configuration.

### Verification and negative controls

Positive evidence is insufficient on its own. Also retain the results of these attempts:

- a repository admin tries to remove a required check — expect refusal;
- a pull request with a failing gate is merged by an administrator — expect refusal, and
  note that with repository-level protection alone this attempt **succeeds**, which is
  exactly why this control is not repository-level;
- an expired exception is used — expect refusal; and
- a repository is created in scope without configuration — expect the baseline to apply
  anyway.

### Failure and bypass modes

Deleting `.sdlc/` inside the repository removes the local hook; only the central required
check survives that, which is the reason this control matters. Other modes: an exception
that never expires; a required check renamed so protection waits on a name that no longer
reports; a self-hosted runner that can alter the checkout before the gate reads it; and
policy applied to a repository list that new repositories are never added to.

### What this skill does not provide

This skill cannot create, administer or attest an organisation policy plane, and cannot
detect from inside a repository whether one governs it. Its own hook is bypassable by
anyone who can edit the repository, and its CI gate is only as binding as the central
policy that requires it. This control is **not provided by this skill**.

---

## Control 2 — External tamper-evident audit sink

### Owner and boundary

**Owner:** the security or compliance function that owns evidence retention, with the
cloud or storage function that owns the retention configuration.

This control is **enterprise-owned**. The boundary is custody: the audit trail this skill
produces is git history *in the repository being governed*, and the governed party can
rewrite it. Self-audit is not audit. An auditable record must leave the administrative
boundary of the party it describes, promptly and automatically.

### Minimum required properties

1. **Export outside the governed party's control.** Events land in a store whose delete
   and retention rights belong to a different principal than the engineers and repository
   admins being audited.
2. **Append-only or WORM retention.** Once written, a record cannot be altered or removed
   before its retention expires — including by the account that wrote it.
3. **Integrity and time provenance.** Each record carries a verifiable digest and a
   trusted timestamp, so a later reconstruction is distinguishable from the original.
4. **Access separation.** Read, write, configure and delete are distinct grants; no single
   role holds all four.
5. **Documented retention and disposal.** The window is written down, matches policy, and
   disposal is a recorded event rather than a silent gap.
6. **Tested retrieval.** A query for a specific historical decision returns it within a
   stated time, proven by rehearsal rather than assumed.
7. **Evidence for denied and failed export.** A dropped, refused or delayed export is
   itself visible; silence must never be indistinguishable from "nothing happened".

### Acceptance contract

The control is accepted when the enterprise can show that: an artifact acceptance and a
gate decision in a governed repository appear in the external store without any action by
the repository's owner; an attempt to delete or edit one of those records before retention
expiry is refused; a rewritten git history in the governed repository does **not** alter
the external record; a named auditor can retrieve a specific decision from a stated date;
and an induced export failure produces an alert rather than a gap.

### Reference architecture (non-normative)

One implementation: forge **audit-log streaming** into object storage with **WORM
retention** — for example S3 Object Lock in compliance mode in a separate account whose
retention policy the engineering organisation cannot alter — with digests recorded and a
monitored alarm on stream interruption. A managed SIEM with immutable retention, or an
append-only transparency log, satisfies the contract equally.

### Evidence package

Retain: the streaming configuration and its destination; the retention/lock configuration
showing the mode and duration; the access policy showing separation of roles; a sample
record set for a known decision with digests; the retrieval rehearsal result with
timestamps; and the alert record from the induced failure test.

### Verification and negative controls

Attempt, and retain the outcome of: deleting a locked record as the writing account
(expect refusal); shortening the retention window as the engineering account (expect
refusal); force-pushing the governed repository's history and re-querying the external
store (expect the record unchanged); and interrupting the export path (expect an alert
inside the stated detection time).

### Failure and bypass modes

Streaming configured but never verified; retention set in governance mode where a
privileged role can still delete; the destination account administered by the same team
being audited; digests computed after ingestion so a substituted record verifies against
itself; and retention shorter than the audit period being claimed.

### What this skill does not provide

This skill emits no audit stream, holds no evidence outside the repository, and cannot make
its own git history tamper-evident to the party that controls the repository. Its artifact
chain is an input to an audit trail, not an audit trail. This control is **not provided by
this skill**.

---

## Control 3 — Independent assurance

### Owner and boundary

**Owner:** an assessor with no authorship interest in this skill — an internal security
function outside the adopting team, or an external firm — engaged by the risk owner rather
than by the implementer.

This control is **enterprise-owned**. The boundary is independence itself, which is a
property of *who* performed the work and cannot be manufactured from inside the work. Every
test in this repository was written by the same author as the implementation. Those tests
are real evidence about behaviour and are worth reading; they are not assurance, because
the author's own blind spots are shared by the author's own tests.

### Minimum required properties

1. **Stated independence and scope.** The assessor's relationship to the authors, the
   scope assessed, and the scope explicitly excluded are all written down.
2. **A named commit under review.** Findings are bound to a specific commit and release,
   because a report about "the skill" expires silently on the next merge.
3. **Threat model review.** The assessor evaluates the threat model rather than accepting
   it, and records disagreement with it.
4. **Control design and adversarial testing.** Both are required: that the control is
   designed to work, and that a motivated engineer attempting to ship an ungoverned change
   was actually resisted. Prompt-injection paths and the review surface are in scope.
5. **Severity and closure evidence.** Each finding carries a severity, a disposition, and
   evidence for the claim that it is closed — not an assertion that it was addressed.
6. **Expiry or reassessment trigger.** The report states what invalidates it: elapsed
   time, an enforcement-generation change, or a change to the gate's authority.

### Acceptance contract

The control is accepted when a report exists that names the assessor and their
independence, binds findings to a commit under review, covers control design and
adversarial attempts as well as the threat model, carries severities with closure
evidence, and declares its own expiry. Absent such a report, the enterprise-wide and
regulated adoption positions remain unmet regardless of how green this repository's CI is.

### Reference architecture (non-normative)

One implementation: a scoped third-party penetration test and control-design review against
a tagged release, followed by an internal security review of the findings by a function
outside the adopting team, repeated on each enforcement-generation change. An internal
red-team exercise by an unrelated group, or a formal audit under a recognised framework,
satisfies the contract equally.

### Evidence package

Retain: the engagement letter or scope document with the independence statement; the report
bound to a commit and release; the finding register with severities and dispositions; the
evidence supporting each closure; the retest result; and the declared expiry or
reassessment trigger.

### Verification and negative controls

Confirm that the report's commit matches the release actually deployed; retest at least
the highest-severity finding and retain the result; and record an adversarial attempt that
the assessor made and the control **survived**, so the report demonstrates resistance
rather than only enumerating weaknesses.

### Failure and bypass modes

Self-assessment presented as independent review; a badge or a passing CI run offered in
place of a report; a report scoped so narrowly that the authority-bearing path was never
examined; findings marked closed with no evidence; and a report kept past its own expiry
while the enforcement generation moved on.

### What this skill does not provide

This skill cannot assess itself. Its suites, mutation proof, SBOM, signatures and
provenance are evidence *inputs* that an assessor may use; none of them is independence,
and no combination of them substitutes for it. **Self-authored tests are not independence.**
This control is **not provided by this skill**.

---

## Adoption checklist by position

| Position | Prerequisites |
|---|---|
| Individual or small team, production use | None beyond this repository. The gate, artifact chain and tests are usable as shipped. |
| Controlled enterprise pilot | All three controls above exist **for the pilot scope**: central policy governs the pilot repositories, decisions export to an external tamper-evident store, and an independent assessment of the pilot's control design exists. |
| Enterprise-wide mandatory control | The three controls operate fleet-wide with drift visibility, plus the operational ownership and telemetry work in `references/enterprise-roadmap.md`. **Not achieved by this project.** |
| Regulated or auditable compliance control | Everything above, plus retention matching the regulatory period, longitudinal operational evidence, and assurance under the applicable framework. **Not achieved by this project.** |

A position may be claimed only when its prerequisites are evidenced. Documenting a
contract is not the same as satisfying it: this file describes what would have to be true,
and says nothing about whether it is true in any particular enterprise.

See `references/limitations.md` for residual risk and `references/enterprise-roadmap.md`
for the work this repository could do on its own.
