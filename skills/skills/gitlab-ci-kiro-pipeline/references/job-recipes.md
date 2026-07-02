# Kiro CI Job Recipes

Nine proven job patterns from the reference pipeline. Each recipe gives the trigger
rules, context-gathering steps, and the tested prompt body. Copy what the user needs
into their `.gitlab-ci.yml`, keep the prompt structure (role → context → numbered
checklist → output format), and tune the checklist to their domain.

All Kiro jobs share this preamble — shown once here, assumed in every recipe:

```yaml
  image: python:3.12-slim
  variables:
    KIRO_API_KEY: $KIRO_API_KEY
  script:
    - apt-get update && apt-get install -y curl git unzip
    - curl -fsSL https://cli.kiro.dev/install | bash
    - export PATH="$HOME/.local/bin:$PATH"
```

And MR-diff jobs share this context step:

```yaml
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD > /tmp/mr-diff.txt
```

## Contents

1. [markdown-lint](#1-markdown-lint) (non-Kiro, lint stage)
2. [pii-check](#2-pii-check) (non-Kiro, security stage)
3. [kiro-code-review](#3-kiro-code-review) (review stage)
4. [kiro-test-failure-analysis](#4-kiro-test-failure-analysis) (analytics, on_failure)
5. [kiro-diff-issue-detection](#5-kiro-diff-issue-detection) (analytics)
6. [kiro-build-failure-remediation](#6-kiro-build-failure-remediation) (analytics, on_failure)
7. [kiro-config-drift-detection](#7-kiro-config-drift-detection) (analytics)
8. [kiro-cross-repo-config-validation](#8-kiro-cross-repo-config-validation) (analytics)
9. [kiro-duplication-sync-check](#9-kiro-duplication-sync-check) (analytics, gating variant)
10. [kiro-change-impact-analysis](#10-kiro-change-impact-analysis) (analytics)
11. [kiro-sonarqube-mcp-review](#11-kiro-sonarqube-mcp-review) (review stage, MCP-integrated)
12. [kiro-mcp-integration-test](#12-kiro-mcp-integration-test) (MCP smoke test, no infrastructure needed)

---

## 1. markdown-lint

Cheap deterministic lint before spending AI credits. Keep deterministic checks in
front of AI checks — they're free and their output feeds the failure-analysis jobs.

```yaml
markdown-lint:
  stage: lint
  image: node:20-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - npx markdownlint-cli2 "**/*.md" 2>&1 | tee /tmp/lint-results.txt || true
    - echo "Lint complete. See above for any issues."
  allow_failure: true
```

## 2. pii-check

Deterministic secrets + PII scan. Runs `detect-secrets` and greps for emails,
12-digit AWS account IDs, and SSN patterns. No AI — regexes are cheaper and stricter
for this. **Defaults to `allow_failure: false`** (zero-tolerance: prefer false
positives over a leaked credential merging in) — unlike the AI-judgment jobs
elsewhere in this catalog, a secrets/PII match is a binary fact, not a subjective
call, so there is no "advisory trust-building period" that makes sense here.

Suppress false positives without disabling the gate:

- **`detect-secrets`**: generate and commit a baseline once
  (`detect-secrets scan > .secrets.baseline`, reviewed by a human), then scan
  against it (`detect-secrets scan --baseline .secrets.baseline`) so known
  fixture/demo secrets are allow-listed by content hash instead of the whole
  check being soft.
- **Custom regex section** (emails/account-IDs/SSNs): add path exclusions for
  known fixture/demo locations (`grep -v '/test/' | grep -v '/fixtures/' | grep -v '/__mocks__/'`)
  rather than loosening the patterns themselves.
- If a team genuinely needs a short tuning period to build out the exclusion
  list against their specific repo, state an explicit end date for the
  `allow_failure: true` window (e.g. "advisory for two weeks, then gating") —
  never leave it open-ended, since teams that copy this recipe rarely revisit
  a setting that isn't blocking anything.

```yaml
pii-check:
  stage: security
  image: python:3.12-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - pip install --quiet detect-secrets
    - |
      FAILED=0
      echo "=== Scanning for secrets/credentials ==="
      detect-secrets scan --all-files --exclude-files '\.git' > /tmp/secrets-report.json
      python3 -c "
      import json
      with open('/tmp/secrets-report.json') as f:
          data = json.load(f)
      results = data.get('results', {})
      total = sum(len(v) for v in results.values())
      if total > 0:
          print(f'Found {total} potential secret(s):')
          for file, findings in results.items():
              for finding in findings:
                  print(f'  - {file}:{finding[\"line_number\"]} [{finding[\"type\"]}]')
      exit(1 if total > 0 else 0)
      " || FAILED=1
      echo "=== Scanning for PII patterns ==="
      PII_FOUND=0
      # Emails (exclude example.com, git SSH URLs, placeholders, fixture/demo paths)
      if grep -rn --include="*.md" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.json" \
        -E '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' . \
        | grep -v 'example\.com' | grep -v 'node_modules' | grep -v '\.git/' | grep -v 'git@' | grep -v 'placeholder' \
        | grep -v '/test/' | grep -v '/fixtures/' | grep -v '/__mocks__/'; then
        PII_FOUND=1
      fi
      # AWS account IDs (12 digits standalone)
      if grep -rn --include="*.md" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.json" \
        -E '\b[0-9]{12}\b' . | grep -v '\.git/' | grep -v 'node_modules' | grep -v 'sha256' \
        | grep -v '/test/' | grep -v '/fixtures/' | grep -v '/__mocks__/'; then
        PII_FOUND=1
      fi
      # SSN patterns
      if grep -rn --include="*.md" --include="*.py" --include="*.yml" --include="*.yaml" --include="*.json" \
        -E '\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b' . | grep -v '\.git/' \
        | grep -v '/test/' | grep -v '/fixtures/' | grep -v '/__mocks__/'; then
        PII_FOUND=1
      fi
      [ "$PII_FOUND" -eq 1 ] && FAILED=1
      [ "$FAILED" -eq 1 ] && { echo "Security scan found issues."; exit 1; }
      echo "All security checks passed."
  allow_failure: false
```

## 3. kiro-code-review

Two sequential passes over the same diff — a security review and a quality review.
Separate prompts beat one mega-prompt: each role stays focused and the output is
two clean reports.

```yaml
kiro-code-review:
  stage: review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  # ...preamble + diff step...
  script:
    - |
      DIFF=$(cat /tmp/mr-diff.txt | head -500)
      kiro-cli chat --no-interactive --trust-tools=read,grep \
        "You are a senior security reviewer. Here is the MR diff:

      $DIFF

      Review for: 1) Hardcoded secrets or API keys 2) Input validation gaps 3) Unsafe deserialization or injection risks 4) Missing error handling that could leak sensitive info 5) AWS credential handling issues. Format as a concise markdown report with severity levels." \
        > /tmp/review-security.md 2>&1 || true
    - |
      DIFF=$(cat /tmp/mr-diff.txt | head -500)
      kiro-cli chat --no-interactive --trust-tools=read,grep \
        "You are a senior code reviewer. Here is the MR diff:

      $DIFF

      Review for: 1) Bugs or logic errors 2) Code style inconsistencies 3) Missing error handling 4) Performance concerns 5) Suggestions for improvement. Be concise, only comment on real issues." \
        > /tmp/review-quality.md 2>&1 || true
    - echo "## Security Review" && cat /tmp/review-security.md
    - echo "## Code Quality Review" && cat /tmp/review-quality.md
```

## 4. kiro-test-failure-analysis

Runs only when an earlier stage failed. Collects whatever test/lint output exists in
the workspace and asks for root cause. Note: files another job wrote to `/tmp` are
gone — use `artifacts:` on the producing job if you need its outputs here.

```yaml
kiro-test-failure-analysis:
  stage: analytics
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: on_failure
  # ...preamble...
  script:
    - |
      CONTEXT=""
      [ -f /tmp/lint-results.txt ] && CONTEXT="$CONTEXT\n--- Lint Results ---\n$(cat /tmp/lint-results.txt | tail -100)"
      for f in $(find . -name "*.log" -o -name "test-results.*" -o -name "junit*.xml" 2>/dev/null | head -5); do
        CONTEXT="$CONTEXT\n--- $f ---\n$(cat "$f" | tail -80)"
      done
      [ -z "$CONTEXT" ] && CONTEXT="No test output files found. Pipeline failed in an earlier stage."
      kiro-cli chat --no-interactive \
        "You are a CI/CD root cause analyst. The pipeline failed. Analyze these test/lint outputs and: 1) Identify the root cause 2) Suggest specific fixes 3) Rate severity (critical/high/medium/low).

      $CONTEXT" 2>&1 | tee /tmp/test-analysis.md || true
  allow_failure: true
```

## 5. kiro-diff-issue-detection

Pre-merge hunt for latent production failures in the diff itself.

Prompt body:

```
You are a root cause prevention analyst. Review this merge request diff for
potential issues that could cause production failures:

$DIFF

Identify: 1) Race conditions or concurrency issues 2) Unhandled edge cases
3) Breaking changes to APIs or configs 4) Resource leaks or missing cleanup
5) Dependency conflicts. Output a risk assessment table with issue, severity,
and recommended fix.
```

Standard MR rules, preamble + diff step, `--trust-tools=read,grep`,
`allow_failure: true`.

## 6. kiro-build-failure-remediation

Like recipe 4 but broader: runs on failure of MR pipelines AND the default branch,
and feeds commit/pipeline metadata rather than test output.

```yaml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: on_failure
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: on_failure
```

Context to gather: `$CI_COMMIT_BRANCH`, `$CI_COMMIT_SHORT_SHA`, `$CI_COMMIT_AUTHOR`,
`$CI_COMMIT_MESSAGE`, `$CI_PIPELINE_URL`, plus `tail -50` of any `*.log` files.

Prompt body:

```
You are a build failure investigator. The CI/CD pipeline has failed. Given this
context:

$CONTEXT

Provide: 1) Most likely root cause 2) Step-by-step remediation instructions
3) Commands to run locally to reproduce and fix 4) Preventive measures to avoid
recurrence. Be specific and actionable.
```

## 7. kiro-config-drift-detection

Targets the classic failure: env vars added to dev/UAT config but forgotten in prod.
Gathers all config-ish files (`*.env`, `.env*`, `*config*`, `*settings*`,
`application*`, `appsettings*` — `head -100` each, cap at ~20 files) plus the diff.

Prompt body:

```
You are a configuration drift analyst. A common production failure pattern is:
environment variables or config keys are added to dev/UAT config files but
forgotten in production config files.

Here is the MR diff:
$DIFF

Here are the config files in this repo:
$CONFIG_CONTENT

Analyze for:
1) Any NEW env vars or config keys added in dev/staging/UAT files that are
   MISSING from production equivalents
2) Any config values that differ between environments in ways that look
   unintentional (typos, stale values)
3) Any config keys in the diff that don't appear in all environment variants

Output a table: | Config Key | Present In | Missing From | Risk Level |
Then provide specific remediation steps. If no drift is found, confirm all
environments are in sync.
```

To gate this recipe, append to the prompt:

```
End your output with exactly one line, once:
CONFIG_DRIFT_VERDICT=DRIFT_FOUND or CONFIG_DRIFT_VERDICT=OK
Output DRIFT_FOUND only for finding class 1 (new keys missing from production).
Typos and stale values (classes 2-3) are advisory — report them but still emit OK.
```

then grep for `CONFIG_DRIFT_VERDICT=DRIFT_FOUND` and `exit 1`, with
`allow_failure: false` (same pattern as recipe 9). The scoping line matters:
without it, soft findings block merges and the team disables the gate.

## 8. kiro-cross-repo-config-validation

For orgs where infra config lives in a separate repo from application code. In
production, clone the infra repo first (needs a deploy token or CI job token with
access); the agent then cross-references with its own `read`/`grep` tools instead of
embedded content:

```yaml
    - git clone https://gitlab-ci-token:${CI_JOB_TOKEN}@gitlab.example.com/team/infra-config.git /tmp/infra-config
```

Prompt body (adjust paths to the real layout):

```
You are a cross-repository configuration validator. In this organization,
environment variables are managed in a SEPARATE repository (infra-config/) by the
platform team, while application code references these variables.

Your task:
1. Read all files in <infra-config-path>/ to find what env vars are defined per environment
2. Read <app-path>/config.py to find what env vars the application CODE expects
3. Read all service files to find any os.getenv() or os.environ references
4. Cross-reference: identify env vars that the application code requires but are
   MISSING from <infra-config-path>/production.env

Output:
## Cross-Repository Config Validation Report
### Env Vars Required by Application Code
### Env Vars Defined in production.env
### MISSING IN PRODUCTION
| Variable | Required By | Exists in UAT? | Impact if Missing |
### Recommendations
```

This recipe relies on `--trust-tools=read,grep` — the agent does the reading itself,
so nothing needs truncating.

## 9. kiro-duplication-sync-check

Catches fixes applied to one copy of duplicated code but not its twins. Shell finds
same-named files; the agent compares content. This is the recipe most worth
**gating** — a missed sync is concrete and checkable, and false positives are rare.

```yaml
kiro-duplication-sync-check:
  stage: analytics
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  # ...preamble + diff step...
  script:
    - |
      DIFF=$(cat /tmp/mr-diff.txt | head -500)
      MODIFIED_FILES=$(git diff --name-only origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD)
      SIMILAR_CONTEXT=""
      for f in $MODIFIED_FILES; do
        [ ! -f "$f" ] && continue
        basename=$(basename "$f")
        similar=$(find . -name "$basename" -not -path "./.git/*" -not -path "$f" 2>/dev/null | head -5)
        [ -n "$similar" ] && SIMILAR_CONTEXT="$SIMILAR_CONTEXT
      Modified: $f
      Similar files: $similar"
      done
      kiro-cli chat --no-interactive --trust-tools=read,grep \
        "You are a code duplication analyst. A common production failure: developers change code in one location but miss updating duplicate or near-duplicate code elsewhere.

      MR Diff:
      $DIFF

      Files with similar names found in repo:
      $SIMILAR_CONTEXT

      Analyze for:
      1) Functions, classes, or logic blocks in the diff that appear duplicated elsewhere in the codebase
      2) Changes made to one file that should likely be mirrored in similar files (e.g., handlers, routes, validators)
      3) Copy-paste patterns where a fix was applied to one instance but not others

      Use the read and grep tools to inspect suspicious files. Output:
      | Changed Code | Location | Potential Duplicate | Sync Needed? |
      Provide specific file paths and line references.

      End your output with exactly one line, once:
      DUPLICATION_VERDICT=SYNC_NEEDED or DUPLICATION_VERDICT=OK" \
        2>&1 | tee /tmp/duplication-check.md || true
    - |
      # Gate: fail the job (and block the merge) when an un-synced duplicate is found.
      if grep -q "DUPLICATION_VERDICT=SYNC_NEEDED" /tmp/duplication-check.md; then
        echo "❌ A change was not mirrored in a duplicate/similar file. Blocking merge."
        echo "   Sync the duplicate(s) listed above (or de-duplicate into a shared module)."
        exit 1
      fi
  allow_failure: false   # advisory variant: drop the gate step and set true
```

## 10. kiro-change-impact-analysis

Manager-facing go/no-go risk report. Feeds diff stats, file list, and commit count
alongside the truncated diff.

Context: `git diff --stat`, `git diff --name-only`, `git rev-list --count` over the
`target...HEAD` range.

Prompt body:

```
You are a change impact analyst helping engineering managers assess deployment
risk. Classify this merge request for a go/no-go deployment decision.

Diff stats:
$STAT

Files changed:
$FILES_CHANGED

Commits in MR: $COMMIT_COUNT

Full diff (truncated):
$DIFF

Provide this structured assessment:

## Risk Summary
**Overall Risk Level**: [CRITICAL / HIGH / MEDIUM / LOW]
**Deployment Recommendation**: [HOLD / PROCEED WITH CAUTION / SAFE TO DEPLOY]

## Impact Breakdown
| Category | Risk | Rationale |
|----------|------|-----------|
| Data/Schema changes | | |
| API/Interface changes | | |
| Infrastructure/Config | | |
| Business logic | | |
| Dependencies | | |

## Blast Radius
- Services affected:
- User-facing impact:
- Rollback complexity: [Simple / Moderate / Complex]

## Recommendations
- Pre-deployment checks:
- Monitoring to watch:
- Rollback plan:

Be concise and actionable. Engineering managers need a quick risk decision.
```

To gate on it, add an output contract (`IMPACT_VERDICT=HOLD|CAUTION|SAFE`) and fail
on `HOLD`, same pattern as recipe 9.

## 11. kiro-sonarqube-mcp-review

MCP-integrated review: the agent queries the customer's SonarQube via its MCP server
and fuses those findings with its own diff review. The pattern generalizes to any
customer MCP server (Jira, internal scanners, observability) — swap the `mcpServers`
entry, the trusted tool name, and the query instruction.

Prerequisites: `SONARQUBE_URL` and `SONARQUBE_TOKEN` as masked CI/CD variables;
Node.js in the image (the server launches via `npx`). MCP config details:
`kiro-cli-headless.md`.

Scope note — worth repeating to the customer: SonarQube provides **SAST** (static
analysis). It does not perform **DAST**. The prompt below makes the agent label its
report accordingly; if dynamic testing is required, add a separate DAST job (e.g.
OWASP ZAP against a deployed review app) — that is outside what this recipe covers.

```yaml
kiro-sonarqube-mcp-review:
  stage: review
  image: python:3.12-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    KIRO_API_KEY: $KIRO_API_KEY
  script:
    - apt-get update && apt-get install -y curl git unzip nodejs npm
    - curl -fsSL https://cli.kiro.dev/install | bash
    - export PATH="$HOME/.local/bin:$PATH"
    - mkdir -p .kiro/settings
    - |
      cat > .kiro/settings/mcp.json <<EOF
      {
        "mcpServers": {
          "sonarqube": {
            "command": "npx",
            "args": ["-y", "sonarqube-mcp-server@latest"],
            "env": {
              "SONARQUBE_URL": "${SONARQUBE_URL}",
              "SONARQUBE_TOKEN": "${SONARQUBE_TOKEN}"
            },
            "disabled": false
          }
        }
      }
      EOF
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD > /tmp/mr-diff.txt
    - |
      DIFF=$(cat /tmp/mr-diff.txt | head -500)
      kiro-cli chat --no-interactive --require-mcp-startup \
        --trust-tools=read,grep,@sonarqube \
        "You are a security reviewer with access to this project's SonarQube instance via MCP tools.

      Here is the MR diff:

      $DIFF

      Steps:
      1) Query SonarQube for open issues, security hotspots, and quality gate status for project '$CI_PROJECT_NAME'
      2) Cross-reference: which SonarQube findings touch files changed in this diff?
      3) Add your own review of the diff for issues SonarQube's rules would miss (business-logic flaws, secrets, auth gaps)

      Output a markdown report with sections: ## SonarQube Findings (state the quality gate status and cite issue keys), ## Diff-Correlated Findings, ## Additional AI Review Findings — each with severity levels.

      End the report with this exact scope statement:
      'Coverage: SAST (SonarQube) + AI static review of the diff. No DAST (dynamic testing of the running application) was performed.'" \
        2>&1 | tee sonarqube-review.md || true
  artifacts:
    paths: [sonarqube-review.md]
    when: always
    expire_in: 1 week
  allow_failure: true
```

Why the specific choices:

- `--require-mcp-startup` — if the SonarQube server can't connect (bad token, no
  network egress), the job fails immediately with a clear error instead of the agent
  producing a review that silently never consulted SonarQube.
- `--trust-tools=read,grep,@sonarqube` — MCP tools are referenced as
  `@server_name` (all tools) or `@server_name/tool_name` (one tool); they must be
  trusted explicitly since headless mode has nobody to approve them. Trust only
  read/query servers in review jobs — never an MCP tool that can mutate state.
- The numbered steps + "cite issue keys" force real tool use; the fixed scope
  statement keeps the report honest about SAST-vs-DAST coverage.

To gate on the quality gate: add an output contract
(`SONAR_VERDICT=GATE_FAILED or SONAR_VERDICT=OK`, emit GATE_FAILED only when
SonarQube's quality gate status is failed) and grep + `exit 1`, same pattern as
recipe 9.

## 12. kiro-mcp-integration-test

Self-verifying smoke test for MCP-in-CI mechanics using the managed **AWS Knowledge
MCP server** — HTTP type, no auth, no infrastructure to host, so it can run in any
pipeline with internet egress. Run this FIRST when introducing MCP to a customer
pipeline: once green, it proves mcp.json config, `--require-mcp-startup`, `@server`
tool trusting, and real tool invocation all work on their runners; swapping in
SonarQube or another customer server is then just a config change.

Validated live (2026-07, real GitLab MR pipeline): agent called
`search_documentation` + `read_documentation`, cited its arguments and source URL,
emitted the verdict line; 25s agent time, 0.45 credits.

```yaml
kiro-mcp-integration-test:
  stage: review
  image: python:3.12-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    KIRO_API_KEY: $KIRO_API_KEY
  script:
    - apt-get update && apt-get install -y curl git unzip
    - curl -fsSL https://cli.kiro.dev/install | bash
    - export PATH="$HOME/.local/bin:$PATH"
    - kiro-cli --version
    - mkdir -p .kiro/settings
    - |
      cat > .kiro/settings/mcp.json <<'MCPEOF'
      {
        "mcpServers": {
          "aws-knowledge": {
            "type": "http",
            "url": "https://knowledge-mcp.global.api.aws",
            "disabled": false
          }
        }
      }
      MCPEOF
    - |
      kiro-cli chat --no-interactive --require-mcp-startup \
        --trust-tools=@aws-knowledge \
        "You have access to the AWS Knowledge MCP server. This is an integration test proving MCP tools work in this CI pipeline.

      Steps:
      1) Call the search_documentation tool with a query about 'S3 bucket versioning'
      2) Call the read_documentation tool on the top result
      3) Summarize in 3 bullet points what S3 versioning does, citing the documentation URL you read

      Rules:
      - You MUST use the MCP tools; do not answer from your own knowledge.
      - In your report, state exactly which MCP tools you called and with what arguments.
      - End your output with exactly one line, once:
        MCP_TEST_VERDICT=TOOLS_USED (if you successfully called the MCP tools)
        or MCP_TEST_VERDICT=TOOLS_FAILED (if any MCP tool call failed)" \
        2>&1 | tee mcp-test-report.md || true
    - |
      echo "=== Gate: verify MCP tools were actually used ==="
      if grep -q "MCP_TEST_VERDICT=TOOLS_USED" mcp-test-report.md; then
        echo "✅ MCP integration test PASSED."
      else
        echo "❌ MCP integration test FAILED: agent did not confirm MCP tool usage."
        exit 1
      fi
  artifacts:
    paths: [mcp-test-report.md]
    when: always
    expire_in: 1 week
  allow_failure: false
```

Why the prompt is structured this way: "do not answer from your own knowledge" plus
"state which tools you called" prevents the one false-positive mode — a model that
answers the S3 question from memory without touching MCP. The verdict gate then
makes the job's green/red state trustworthy. Note the observed tool naming in logs:
Kiro surfaces MCP tools as e.g. `aws___read_documentation (from mcp server:
aws-knowledge)`; you trust them at the server level with `@aws-knowledge`.
