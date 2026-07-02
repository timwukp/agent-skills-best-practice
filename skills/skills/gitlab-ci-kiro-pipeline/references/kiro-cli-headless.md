# Kiro CLI Headless Mode Reference

How to run Kiro CLI non-interactively inside CI containers. Verified against a
real GitLab reference pipeline (python:3.12-slim runners, 2026).

## Install

```bash
apt-get update && apt-get install -y curl git unzip   # slim images lack these
curl -fsSL https://cli.kiro.dev/install | bash
export PATH="$HOME/.local/bin:$PATH"
kiro-cli --version                                    # sanity check
```

The installer puts the binary in `~/.local/bin`. Install takes ~20–30s per job on a
slim image. For pipelines with many Kiro jobs, bake a base image instead:

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y curl git unzip \
 && curl -fsSL https://cli.kiro.dev/install | bash
ENV PATH="/root/.local/bin:${PATH}"
```

## Authentication

Headless mode authenticates with an API key from the environment:

```yaml
variables:
  KIRO_API_KEY: $KIRO_API_KEY
```

Set `KIRO_API_KEY` as a **masked** (and usually **protected**) CI/CD variable in
GitLab → Settings → CI/CD → Variables. Gotchas:

- Protected variables are invisible to pipelines on unprotected branches — MR
  pipelines from feature branches will fail auth. Either unprotect the variable or
  protect the branches.
- Masking requires the value to meet GitLab's masking rules (single line, ≥8 chars).
- Never echo the key; never pass it as a command-line argument (visible in `ps`).

## Headless invocation

```bash
kiro-cli chat --no-interactive --trust-tools=read,grep "PROMPT" 2>&1 | tee /tmp/out.md || true
```

- `chat --no-interactive` — run one prompt, print the response, exit. This is the
  headless mode: no TTY, no session. Omitting it makes the job hang until timeout.
- `--trust-tools=read,grep` — pre-approve exactly these agent tools. In interactive
  use Kiro asks before each tool call; headless there is nobody to ask, so any tool
  not trusted either fails or blocks. `read,grep` is the right grant for review
  jobs: the agent can inspect the checked-out repo but cannot modify it or execute
  commands. There is also `--trust-all-tools` — do not use it in CI; a prompt-injected
  diff could then make the agent run arbitrary commands on your runner.
- `--require-mcp-startup` — fail immediately if any configured MCP server fails to
  connect. Always set this when the job depends on MCP servers (see MCP section
  below); without it a dead server means the agent silently proceeds without its
  tools or the job hangs.
- Prompts without any tool needs (pure analysis of embedded text) can omit
  `--trust-tools` entirely.
- `2>&1 | tee` — capture the full response to a file for later steps (verdict
  grepping, artifacts) while still streaming to the job log.
- `|| true` — a transient API/network failure should not fail an advisory job.
  Gate on grepped verdict lines instead (see SKILL.md).

## Feeding context

Embed context directly in the prompt for anything bounded and known up front:

```bash
DIFF=$(cat /tmp/mr-diff.txt | head -500)
kiro-cli chat --no-interactive --trust-tools=read,grep \
  "You are a senior code reviewer. Here is the MR diff:

$DIFF

Review for: 1) ... 2) ..."
```

Rules of thumb:

- **Truncate everything you embed**: `head -500` for diffs, `tail -100` for logs,
  `head -100` per config file. Unbounded input inflates cost and can exceed context.
- For large repos, embed only `git diff --stat` + the file list, and tell the agent
  to use `read`/`grep` to inspect specific files itself — that's what the trusted
  tools are for.
- Shell-expanded variables inside the double-quoted prompt (`$DIFF`, `$CI_COMMIT_SHA`)
  work fine inside a YAML `|` block; write the whole invocation inside one
  `- |` script item so quoting stays sane.

## MCP servers in CI jobs

Kiro CLI loads MCP servers from `mcp.json` — workspace level
`<project-root>/.kiro/settings/mcp.json` (wins on name conflicts) or global
`~/.kiro/settings/mcp.json`. In CI, either commit the workspace file or write it in
the job script; inject credentials from masked CI/CD variables via `env`:

```yaml
  script:
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
```

HTTP-based servers use `"type": "http"` + `"url"` instead of `command`/`args`.
`kiro-cli mcp add --name ... --command ... --args ... --env ...` is the CLI
alternative to writing the file. The runner image needs whatever runtime the server
launches with (`npx` → install Node in the job, `uvx` → install uv/Python).

Headless rules for MCP:

- **`--require-mcp-startup`** on the `chat` call whenever the prompt depends on MCP
  tools. Default behavior tolerates a server that fails to connect — the agent then
  "reviews" without the scanner and the report looks complete but isn't, or the job
  hangs waiting. Fail fast instead; a red job with a connection error is debuggable,
  a plausible-but-toolless review is not.
- **Trust the MCP tools explicitly**: MCP tools are named `@server_name` (all of a
  server's tools) or `@server_name/tool_name` (one tool, wildcards like
  `@server/read_*` supported) — add them to `--trust-tools`
  (e.g. `--trust-tools=read,grep,@sonarqube`). Nothing can approve interactively in
  headless mode. Trust only the specific servers/tools the prompt needs — an MCP
  tool that can mutate state (create Jira tickets, trigger deploys) should not be
  trusted in a review job at all.
- **Tell the agent to use the server and to cite it.** Models won't reliably call an
  unfamiliar tool unprompted; the prompt should name the action ("Query SonarQube
  for open findings on project X") and require the report to state which tool data
  it used.

Capability honesty: an MCP integration adds exactly what the backing tool does, no
more. SonarQube MCP = SAST (static analysis of source); it does NOT provide DAST
(testing the running app). If the customer needs DAST, add a conventional job
(e.g. OWASP ZAP against a review environment) — don't let the AI job's report imply
dynamic coverage it doesn't have. Ask the same question of any customer MCP server
before wiring it in: what does this tool actually check?

## Machine-readable verdicts

To let the shell act on the agent's conclusion, put an output contract in the prompt:

```
End your output with exactly one line: VERDICT=PASS or VERDICT=FAIL
```

then:

```bash
grep -q "VERDICT=FAIL" /tmp/out.md && exit 1
```

Grep for the exact token, not prose. Keep the token unusual enough that it can't
appear incidentally in the analysis body (prefix it, e.g. `DUPLICATION_VERDICT=`).

## Cost and runtime expectations

Observed in the reference pipeline (500-line diff, read/grep over a small repo):

| Job type | Wall time | Credits |
|---|---|---|
| Single-prompt diff review | 15–60s agent time | ~0.1–0.3 |
| Repo-crawling analysis (read+grep) | 60–105s | ~0.3–0.8 |

Add ~30s per job for apt+install. A five-Kiro-job MR pipeline lands around 4 minutes
total with default runner concurrency.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Job hangs then times out | Missing `--no-interactive`, or agent waiting on untrusted tool | Add flag; align `--trust-tools` with what the prompt asks |
| Auth error after install | `KIRO_API_KEY` unset in this pipeline context | Check variable protection vs. branch protection |
| `kiro-cli: command not found` | PATH not exported after install | `export PATH="$HOME/.local/bin:$PATH"` in the same script |
| Empty/garbled review | Diff empty because fetch failed | `git fetch origin $TARGET` first; check `GIT_DEPTH` |
| Response cut off mid-table | Context overflow from unbounded embed | Truncate harder; move detail-gathering to agent tools |
| Verdict grep matches when it shouldn't | Agent quoted the token while explaining the contract | Use a longer prefixed token; instruct "output the line only once" |
| Job fails at startup with MCP connect error | Server unreachable/misconfigured (and `--require-mcp-startup` set — working as intended) | Check server URL/token variables, network egress from runner, runtime (npx/uvx) installed |
| Review never mentions MCP tool data | Tool not trusted, server silently down (no `--require-mcp-startup`), or prompt never asked | Add server to `--trust-tools`, add `--require-mcp-startup`, name the query in the prompt |
