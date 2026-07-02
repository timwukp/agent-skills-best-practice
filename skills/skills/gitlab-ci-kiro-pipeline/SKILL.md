---
name: gitlab-ci-kiro-pipeline
description: Build, extend, or debug GitLab CI/CD pipelines (.gitlab-ci.yml) that run Kiro CLI in headless mode for AI-powered merge-request review, security scanning, test-failure analysis, config-drift detection, code-duplication sync checks, and change-impact/risk analysis — including integrating the customer's MCP servers (SonarQube SAST, Jira, internal tools) into CI jobs. Use this skill whenever the user mentions GitLab CI, .gitlab-ci.yml, GitLab pipelines, merge-request automation, AI code review in CI, Kiro CLI in CI/CD, kiro-cli headless or non-interactive mode, MCP servers in pipelines, or wants agentic/LLM checks in a pipeline — even if they don't say "Kiro" or "GitLab CI" explicitly (e.g. "add an AI reviewer to my MRs", "hook SonarQube into the AI review", "make the pipeline catch config drift").
license: MIT
---

# GitLab CI/CD Pipelines with Kiro CLI Headless Mode

Build `.gitlab-ci.yml` pipelines where Kiro CLI acts as an AI reviewer/analyst on merge requests. The pattern: each job installs Kiro CLI in a throwaway container, gathers context (the MR diff, config files, failure logs), and runs `kiro-cli chat --no-interactive` with a role-scoped prompt. Output goes to the job log and optionally gates the merge.

## Workflow

1. **Understand the repo and goals.** Ask (or infer from the repo) which checks the user wants: advisory review only, or merge-blocking gates? Which languages/config layouts exist? Is there an existing `.gitlab-ci.yml` to extend?
2. **Pick jobs from the recipe catalog.** Read `references/job-recipes.md` for nine proven job patterns (code review, PII/secrets scan, test-failure analysis, diff issue detection, build-failure remediation, config drift, cross-repo config validation, duplication sync check, change-impact analysis). Copy only the ones the user needs.
3. **Start from the template.** `assets/gitlab-ci-template.yml` is a complete, working pipeline skeleton. Adapt stages and jobs rather than writing from scratch.
4. **Decide advisory vs. gating per job** (see below) and set `allow_failure` accordingly.
5. **Verify prerequisites with the user**: the `KIRO_API_KEY` CI/CD variable must be set (masked, protected) in GitLab → Settings → CI/CD → Variables, and confirm your runners have internet access to `https://cli.kiro.dev/install`. If your GitLab Runner sandbox lives inside your VPC and has **NO outbound internet access at all** (no NAT gateway, no internet gateway, no proxy), refer to the "Air-gapped runners" section in `references/kiro-cli-headless.md` for the no-internet VPC approach — the API side works over AWS PrivateLink, but the CLI binary must be staged internally.
6. **Lint before delivering.** If the user has GitLab access, validate with the CI Lint API or `glab ci lint`; otherwise at minimum check YAML validity (`python3 -c "import yaml,sys; yaml.safe_load(open('.gitlab-ci.yml'))"`).

## Core anatomy of a Kiro CI job

Every Kiro job follows this shape. Details and flag reference: `references/kiro-cli-headless.md`.

```yaml
kiro-code-review:
  stage: review
  image: python:3.12-slim
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    KIRO_API_KEY: $KIRO_API_KEY        # masked CI/CD variable; auths headless mode
  script:
    - apt-get update && apt-get install -y curl git unzip
    - curl -fsSL https://cli.kiro.dev/install | bash
    - export PATH="$HOME/.local/bin:$PATH"
    - git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - git diff origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME...HEAD > /tmp/mr-diff.txt
    - |
      DIFF=$(cat /tmp/mr-diff.txt | head -500)
      kiro-cli chat --no-interactive --trust-tools=read,grep \
        "<role-scoped prompt with $DIFF embedded>" \
        2>&1 | tee /tmp/review.md || true
    - cat /tmp/review.md
  allow_failure: true
```

The load-bearing choices, and why:

- **`--no-interactive`** runs a single prompt and exits — this is Kiro CLI's headless mode; without it the job hangs waiting for a TTY.
- **`--trust-tools=read,grep`** grants only read-only tools. The agent can inspect the checked-out repo but cannot edit files or run arbitrary commands inside your runner. Widen this only deliberately.
- **Truncate the diff** (`head -500`) before embedding it in the prompt. Unbounded diffs blow the context window, slow the job, and raise cost. If a diff is routinely bigger, summarize `git diff --stat` first and let the agent use `read`/`grep` to pull details itself.
- **`|| true` inside the script + `allow_failure: true`** keeps advisory jobs from blocking merges when the AI call hiccups. Remove both only for gating jobs (next section).
- **Three-dot diff** (`target...HEAD`) shows only the MR's own changes, not unrelated target-branch drift.
- **A `default: retry` block** (`max: 2, when: runner_system_failure`) absorbs flaky-runner failures without retrying genuine job failures.

## Advisory vs. merge-gating jobs

**Advisory** (default): `allow_failure: true`, findings land in the job log. Safe starting point; humans read and decide.

**Gating**: make the agent's verdict machine-readable, then let the shell decide. Instruct the model to end its output with a verdict line, grep for it, and exit non-zero:

```yaml
  script:
    - |
      kiro-cli chat --no-interactive --trust-tools=read,grep \
        "…analysis prompt… End your output with exactly one line:
         DUPLICATION_VERDICT=SYNC_NEEDED or DUPLICATION_VERDICT=OK" \
        2>&1 | tee /tmp/report.md || true
    - |
      if grep -q "DUPLICATION_VERDICT=SYNC_NEEDED" /tmp/report.md; then
        echo "❌ Change not mirrored in duplicate file. Blocking merge."
        exit 1
      fi
  allow_failure: false
```

Never gate on the raw exit code of `kiro-cli` itself (network errors would block merges) and never parse free-form prose. The verdict-line contract is what makes AI output CI-safe. Start every new job advisory; promote to gating only after the team has watched it run for a while and trusts its judgment — unless the user explicitly asks for a blocking check on day one, in which case build it gated and mention the advisory-first option.

Any recipe in `references/job-recipes.md` can be converted to gating this way: append the verdict contract to its prompt and add the grep step. **Scope the verdict to the blocking-worthy findings only.** If a prompt checks several severities (e.g. config drift also looks for typos and stale values), tell the model explicitly which finding class triggers the failing verdict — otherwise soft findings block merges and the team turns the gate off.

Write gated-job reports to the workspace (not `/tmp`) and attach them so reviewers can read the verdict from the MR page:

```yaml
  artifacts:
    paths: [config-drift-report.md]
    when: always
    expire_in: 1 week
```

## Integrating customer MCP servers (SonarQube, Jira, internal tools)

Kiro CLI can load the customer's MCP servers inside CI jobs, giving the agent live access to their scanners and systems — e.g. pull SonarQube findings into the AI review instead of re-deriving them from the diff. Full config format, tool trusting, and troubleshooting: `references/kiro-cli-headless.md` (MCP section). The essentials:

1. **Write the MCP config in the job** (or commit it): workspace-level `.kiro/settings/mcp.json` with an `mcpServers` entry per server. Pass credentials from masked CI/CD variables via the `env` block — never hardcode them.
2. **Add `--require-mcp-startup` whenever the job depends on an MCP server.** Without it, a server that fails to connect leaves the agent answering without the tools, silently producing a review that looks complete but never consulted the scanner — or the job hangs. With it, the job fails fast with a clear error, which is exactly what you want in CI.
3. **Trust the MCP tools by name** in `--trust-tools` alongside `read,grep`. In headless mode nothing can approve a tool interactively, so an untrusted MCP tool is a dead tool.
4. **Prompt the agent to actually use the server** ("Query SonarQube for open findings on this project, then…") — and to state in its report which tool data it used.

**Scope claims honestly.** An integrated scanner only extends the review as far as that scanner's capability. SonarQube's MCP server provides **SAST** (static analysis of source code) — it does not perform **DAST** (probing the running application). Instruct the agent to label its report accordingly ("Static analysis + AI review; no dynamic testing performed"), and if the customer needs DAST, add a separate conventional CI job (e.g. OWASP ZAP against a deployed review environment) rather than pretending the AI+SAST job covers it. The same principle applies to any customer MCP server: state what the tool checked, not what the job name implies.

Recipe 11 in `references/job-recipes.md` is a complete SonarQube-integrated review job to copy.

**Testing MCP integration without customer infrastructure:** before wiring up a real SonarQube/Jira server, validate the pipeline's MCP mechanics with the managed **AWS Knowledge MCP server** (`https://knowledge-mcp.global.api.aws` — HTTP type, no auth, no hosting, rate-limited). Recipe 12 is a self-verifying smoke-test job (validated live 2026-07): it exercises the identical mechanics (mcp.json, `--require-mcp-startup`, `@server` trusting, verdict gate), so once it's green, swapping in the customer's server is a config change, not a new integration.

## Failure-analysis jobs

Jobs with `when: on_failure` run only after an earlier stage fails — use them to have Kiro read logs and explain the failure:

```yaml
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: on_failure
```

Feed them whatever context survives: `$CI_COMMIT_MESSAGE`, `$CI_PIPELINE_URL`, and any `*.log` / `junit*.xml` files found in the workspace. Note that `/tmp` files do NOT persist across jobs — pass files between jobs with `artifacts:` if a later job needs an earlier job's output.

## Writing the prompts

Each job's prompt gives the agent a **role** ("You are a senior security reviewer"), the **context** (embedded diff/configs/logs), a **numbered checklist** of what to look for, and a **required output format** (markdown table or report with severity levels). Concrete, tested prompt bodies for all nine job types are in `references/job-recipes.md` — reuse them verbatim and tweak the checklists to the user's domain.

## Bundled resources

- `references/job-recipes.md` — full YAML + prompt for each of the nine job patterns; read it when assembling a pipeline.
- `references/kiro-cli-headless.md` — Kiro CLI headless flags, auth, install, cost/runtime expectations, troubleshooting, and air-gapped/PrivateLink-only runner setup (tested end-to-end). Read it when debugging a failing Kiro job, when the user asks about the CLI itself, or when the runner has no internet access.
- `assets/gitlab-ci-template.yml` — complete working pipeline (lint → security → review → analytics → pages) to copy and trim.

## Common pitfalls

- **Missing `KIRO_API_KEY`**: job installs the CLI fine, then the chat call fails auth. Confirm the variable exists and is available on the branch (unprotected branches can't read protected variables).
- **`git diff` fails**: the runner did a shallow clone or the target branch isn't fetched. Always `git fetch origin $CI_MERGE_REQUEST_TARGET_BRANCH_NAME` first; set `GIT_DEPTH: "0"` if history-based analysis is needed.
- **Job hangs**: `--no-interactive` was omitted, or the prompt asked the agent to do something requiring an untrusted tool and it's waiting for approval. Check `--trust-tools` covers everything the prompt implies.
- **YAML quoting bugs**: multi-line prompts with embedded `$DIFF` belong inside a `|` literal block with the prompt in double quotes; dollar-variables you want GitLab to expand stay as-is, ones the shell should expand need the shell block.
- **Every Kiro job re-installs the CLI (~20–30s)**: acceptable for a handful of jobs; if the pipeline grows, build a base image with kiro-cli preinstalled and swap `image:`.
