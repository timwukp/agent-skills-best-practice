# Skill Testing Methodology & Results

How the skills in this repo are tested, and the recorded results for the Secure SDLC and FSI Compliance skill sets (June 2026). Use this as a template for testing your own skills.

## Test Layers

| Layer | What it verifies | Tooling |
|-------|------------------|---------|
| 1. Static validation | Agent Skills spec compliance: frontmatter fields, kebab-case, name==folder, description ≤1024 chars, body ≤500 lines | `skills-workshop/scripts/quick_validate.py` (runs in CI) |
| 2. Blind trigger routing | Does the right skill activate for the right query — and stay silent otherwise? | Judge agents see only the name+description metadata of all skills (simulating Level-1 progressive disclosure) and route shuffled queries from `evals/trigger_evals.json` with ground truth held out |
| 3. Task execution + independent grading | Does the skill produce correct deliverables? | Executor agents run each `evals/evals.json` prompt with only the skill instructions (expectations hidden); separate grader agents mark each expectation PASS/FAIL with evidence |
| 4. Real-environment verification | Does triggering work in actual Claude Code? | Headless `claude -p` on an EC2 test instance (Claude Code 2.1.152, Bedrock backend), skills installed in `~/.claude/skills/`, skill invocations extracted from `--output-format stream-json` |

Key hygiene rules:

- **Hold out ground truth.** Routing judges never see which skill a query belongs to; executors never see the grading expectations. Self-grading is not accepted.
- **Iterate on misses, then re-run the full set.** Description fixes for routing misses must be re-validated against all queries (fresh shuffle), not just the failed ones — fixes can regress neighbors.
- **Fix ambiguity in the eval, not the skill, when the query itself is ambiguous.** Tuning descriptions to win genuinely ambiguous queries is overfitting (see anthropics/skills skill-creator guidance).

## Recorded Results — Secure SDLC + FSI Compliance Skills

### Layer 1: Static validation

All 32 skills pass (including name==folder and 500-line body checks).

### Layer 2: Blind trigger routing (108 queries, 3 independent judges per round)

| Round | Should-trigger recall | False activations | Action taken |
|-------|----------------------|-------------------|--------------|
| v1 | 50/54 (93%) | 0/54 | 4 misses were adjacent-skill ownership ambiguity (security-story-writing vs user-story-writing; sprint-planning vs user-story-writing). Added explicit ownership clauses to two descriptions; disambiguated 2 ambiguous eval queries. |
| v2 (fresh shuffle) | 53/54 (98%) | 0/54 | Remaining miss was a genuinely ambiguous query ("draft the security requirements" — threat identification vs story writing are different skills by design); disambiguated the eval query, verified the contrast triple routes correctly. |
| v3 (fresh shuffle) | 54/54 (100%) | 53/54 | One false fire: "Explain what STRIDE stands for" activated threat-modeling. Accepted as borderline-harmless (educational query lands on the skill that documents STRIDE); recorded rather than tuned away to avoid overfitting. |

### Layer 3: Task execution + independent grading (18 evals)

All 18 task evals **PASS** — every expectation passed under strict independent grading (3 grader agents, evidence required per expectation):

- threat-modeling 3/3, security-story-writing 3/3, sprint-planning 3/3, sprint-security-review 3/3, user-story-writing 3/3, fsi-compliance-checker 3/3.
- Graders additionally spot-checked fsi-compliance-checker outputs against the bundled reference files: no fabricated control IDs found; QSA disclaimer present in all reports.

### Layer 4: Real environment (Claude Code 2.1.152, headless, Bedrock)

Skills installed to `~/.claude/skills/`; one natural-language query per skill plus two should-not-trigger probes; skill invocation read from the session's tool-use stream:

| Query (abridged) | Expected | Triggered |
|------------------|----------|-----------|
| "money transfer API ... threat model it" | threat-modeling | ✅ threat-modeling |
| "turn this into a backlog story: unauthenticated callers..." | security-story-writing | ✅ security-story-writing |
| "plan our sprint: velocity 34/28/31, 2 critical vulns..." | sprint-planning | ✅ sprint-planning |
| "prepare the security section of our sprint review..." | sprint-security-review | ✅ sprint-security-review |
| "split this epic into stories: pay invoices online..." | user-story-writing | ✅ user-story-writing |
| "is this PCI-DSS compliant: we log full card auth request bodies" | fsi-compliance-checker | ⚠️ see below |
| "what is the capital of France?" | none | ✅ none |
| "fix the SQL injection in this code" | none | ✅ none |
| "Singapore bank moving service to another country - MAS TRM implications?" | fsi-compliance-checker | ✅ fsi-compliance-checker (+ loads references/) |
| explicit: "use the fsi-compliance-checker skill: ..." | fsi-compliance-checker | ✅ + correctly loads `references/pci-dss.md` (progressive disclosure verified end-to-end) |

**Known limitation (recorded, not hidden):** queries phrased as "review this change for PCI-DSS" can route to Claude Code's *built-in* `security-review` skill, and short yes/no compliance questions may be answered directly from model knowledge without invoking any skill. Framework-specific phrasing ("MAS TRM implications", "compliance check against PCI-DSS controls") and explicit invocation route correctly. This is an environment-level interaction with built-in skills that description tuning cannot fully override; it is documented in the skill's `evals/README.md`.

## Running the Tests Yourself

```bash
# Layer 1
for d in skills/skills/*/; do python3 skills-workshop/scripts/quick_validate.py "$d"; done

# Layer 4 (requires Claude Code; works headless with Bedrock)
cp -r skills/skills/<skill> ~/.claude/skills/<skill>
claude -p "<a should-trigger query from evals/trigger_evals.json>" \
  --output-format stream-json --verbose | grep -o '"skill":"[^"]*"'
```

Layers 2-3 are agent-orchestrated: any capable agent runner works. The essential structure is (a) routing judges that see only skill metadata + blind queries, and (b) executor/grader separation with expectations hidden from the executor.
