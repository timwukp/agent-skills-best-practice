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

## Air-gapped runners (no internet access, AWS PrivateLink only)

Some enterprise GitLab Runners live inside a VPC with **no NAT gateway and no
internet gateway at all** — only an AWS PrivateLink Interface VPC Endpoint for the
Kiro/Q Developer API. This is a fully supported, **tested and verified** pattern
(see Validation below), but it splits into two independent problems that get
solved differently:

1. **API calls from `kiro-cli chat`** (headless auth + inference) — covered by
   AWS PrivateLink. Fully private, no code changes needed beyond DNS.
2. **The CLI binary itself and its installer script** — NOT covered by PrivateLink.
   `cli.kiro.dev`, `prod.download.cli.kiro.dev` are ordinary internet domains; a
   runner with zero egress cannot reach them. This half requires manually staging
   the binary inside the customer's network.

### Setting up the PrivateLink endpoint

Create an Interface VPC Endpoint for the Kiro/Q Developer service in the VPC that
hosts the runners, with Private DNS enabled:

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id <vpc-id> \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.<region>.q \
  --subnet-ids <subnet-id> \
  --security-group-ids <sg-allowing-443-from-runners> \
  --private-dns-enabled
```

Valid service names (region-dependent): `com.amazonaws.us-east-1.q`,
`com.amazonaws.us-east-1.codewhisperer`, `com.amazonaws.eu-central-1.q`,
`com.amazonaws.us-gov-west-1.q`, `com.amazonaws.us-gov-east-1.q`. With Private DNS
enabled, a single endpoint automatically resolves `q.<region>.amazonaws.com`,
`runtime.<region>.kiro.dev`, `management.<region>.kiro.dev`, and
`telemetry.<region>.kiro.dev` to private IPs inside the VPC — no extra endpoints or
split-horizon DNS config needed for the API side. This does **not** cover
`cli.kiro.dev`, `prod.download.cli.kiro.dev`, or `auth.desktop.kiro.dev` — those
stay on their public IPs and are simply unreachable from a zero-egress subnet
(DNS still resolves; the TCP connection just has nowhere to route).

### Staging the CLI binary internally

Because the installer script (`curl -fsSL https://cli.kiro.dev/install | bash`)
needs internet access it doesn't have in this topology, replace it with a
manual stage-and-fetch step:

1. **On a machine with internet access** (not the runner), pull the version
   manifest and the binary for your target platform, then verify the checksum:
   ```bash
   curl -fsSL https://prod.download.cli.kiro.dev/stable/latest/manifest.json -o manifest.json
   # pick the package matching your platform, e.g. os=linux, architecture=x86_64,
   # fileType=tarGz, variant=headless -> "download": "<version>/kirocli-x86_64-linux.tar.gz"
   curl -fsSL "https://prod.download.cli.kiro.dev/stable/<version>/kirocli-x86_64-linux.tar.gz" -o kirocli.tar.gz
   sha256sum kirocli.tar.gz   # compare against manifest.json's "sha256" field for that package
   ```
2. **Upload the verified binary to an internal artifact store** reachable from
   the runner's VPC without internet — an S3 bucket behind an **S3 Gateway
   Endpoint** (free, private, no NAT needed) is the simplest option; an internal
   Artifactory/Nexus/GitLab Package Registry works the same way.
3. **Change the GitLab job's install step** to pull from the internal store
   instead of the public installer:
   ```yaml
   script:
     - aws s3 cp s3://internal-artifact-bucket/kiro-cli/<version>/kirocli-x86_64-linux.tar.gz .
     - tar -xzf kirocli-x86_64-linux.tar.gz -C /tmp/extract
     - KIRO_CLI_SKIP_SETUP=1 /tmp/extract/kirocli/install.sh
     - export PATH="$HOME/.local/bin:$PATH"
     - kiro-cli --version
   ```
4. **Keep the binary current.** Since updates no longer happen automatically, set
   up a small recurring job (outside the closed VPC) that re-pulls the manifest,
   diffs the version, and re-uploads to the internal store — otherwise runners
   silently drift to a stale CLI version.

### Headless auth still works the same way

Once the binary is staged and PrivateLink is up, authentication is unchanged from
the normal headless flow: set `KIRO_API_KEY` as usual (see Authentication above).
No special air-gapped auth mode is needed — the API key flows over the same
PrivateLink connection as any other `kiro-cli chat` call.

### Validation

This pattern was tested end-to-end in a disposable AWS environment (not a
customer account): an isolated VPC with no Internet Gateway or NAT Gateway, a
`com.amazonaws.<region>.q` PrivateLink endpoint (Private DNS enabled), and a
private-subnet EC2 instance with no public IP. Confirmed working:

- The instance genuinely has no route to the public internet (`cli.kiro.dev`
  resolves to a public IP but is unreachable), while `q.<region>.amazonaws.com`
  resolves to a private IP inside the VPC and is reachable.
- A binary staged via S3 + an S3 Gateway Endpoint (standing in for an internal
  artifact store) installs and runs correctly with a checksum-verified transfer.
- A raw TCP + TLS handshake to `q.<region>.amazonaws.com:443`, independent of
  the CLI, succeeds and terminates at the PrivateLink endpoint (server
  certificate `CN=*.codewhisperer.<region>.vpce.amazonaws.com`).
- `kiro-cli chat --no-interactive` with `KIRO_API_KEY` set returns exit code 0
  with a genuine, metered model response over this path.

Not covered by this test: MCP server behavior and multi-job pipeline mechanics
in this specific air-gapped topology (unaffected by the network path and
already covered by the rest of this skill), and real customer governance
settings under headless mode. Customers should still run their own pipeline
test after wiring this up. Full test methodology, environment design, and
results: `tests/e2e-results/gitlab-ci-kiro-pipeline-airgap-20260702T112000Z/README.md`.

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
| Job hangs at `curl cli.kiro.dev/install` | Runner has no internet egress; PrivateLink only covers API traffic, not the installer | Stage the binary internally — see "Air-gapped runners" above |
| `kiro-cli chat` fails with "Failed to open browser for authentication" | `KIRO_API_KEY` not set — CLI fell back to interactive login, which needs a browser/device the runner doesn't have | Set `KIRO_API_KEY` as shown in Authentication above; headless mode never opens a browser once it's set |
