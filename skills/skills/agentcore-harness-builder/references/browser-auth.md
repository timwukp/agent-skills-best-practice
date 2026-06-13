# Browser — Human-in-the-Loop SSO Login & Long-Running Turns

When the harness Browser tool must reach a page behind **interactive SSO** (IAM Identity Center, Enterprise login, MFA),
the agent can't type the credentials itself. A human completes the login through **AgentCore Browser Live View** while
the agent waits, then the agent resumes against the now-authenticated session. This is the pattern that was battle-
tested building the Amazon Quick POC web-UI test agent — every gotcha below cost real debugging time and most are
undocumented. Related upstream issue: https://github.com/aws/bedrock-agentcore-sdk-python/issues/518.

## Contents
- [The login handoff — do NOT "Take control"](#take-control)
- [S3-signal handoff (stay hands-off, keep the runtime warm)](#s3-signal)
- [Inline-function pause/resume contract for InvokeHarness](#pause-resume)
- [Long read_timeout for waiting turns](#read-timeout)
- [Browser sessions don't persist across turns](#no-persist)
- [Retrieving files the agent wrote (/mnt/reports → S3)](#retrieve-files)

---

## Take control

The agent navigates to the SSO-gated URL; the browser surfaces a login screen. A human opens **Browser Live View** and
logs in **directly** — clicking, typing the username/password, completing MFA.

- **Do NOT click "Take control".** "Take control" followed by "Release" **tears down the automation context** the agent
  is attached to — the agent's page handle goes dead and the authenticated session is lost. Interact with the page
  *directly* in Live View; you do not need to take control to type into the page.
- **The agent must RECONNECT after login** — it must **re-read the page** (a fresh navigate / get_text / snapshot) and
  **not reuse the pre-login page handle**. The handle from before login points at the old (logged-out) context; reusing
  it returns stale content or errors. Once the agent re-reads, the **authenticated session carries over** (cookies live
  in the browser session) and it proceeds normally.

> Rule of thumb: human logs in via Live View → agent throws away its old page reference → agent re-navigates/re-reads →
> authenticated state is there.

---

## S3-signal

To stay **hands-off** while the human logs in (and keep the microVM **warm** so state survives), use an out-of-band
flag in S3 instead of having the agent poll the browser:

1. The agent navigates to the SSO page, then **polls an S3 flag via the `shell` tool** (e.g. `aws s3 ls s3://bucket/login-done`
   in a loop with `sleep`) — **never via the Browser tool**. Polling through the browser risks driving/refreshing the
   page mid-login and disturbing the very context you're trying to preserve; the shell poll leaves the page untouched.
2. The human logs in via Live View, then writes the flag (`aws s3 cp done s3://bucket/login-done`, or any signal file).
3. The agent's next poll sees the flag, stops waiting, **re-reads the page** (see above), and resumes **instantly**.

This keeps the agent autonomous (no per-step prompting), keeps the runtime warm during the human delay, and gives a
clean resume signal. The execution role needs `s3:ListBucket`/`s3:GetObject` on the signal prefix.

---

## Pause-resume

If you'd rather hand control back to your orchestrator (instead of an in-session shell poll), use an **inline function**
(see `tools.md`) such as `request_human_login`. The `InvokeHarness` data-plane contract for this is:

- When the agent calls an inline function, the **stream ends with `stopReason == "tool_use"`** (it does *not* close the
  session). The streamed event carries the `toolUse` block (`toolUseId`, `name`, `input`).
- **Resume by re-invoking the SAME `runtimeSessionId`** (≥33 chars — see `gotchas.md`) with two messages appended:
  1. an **assistant** message containing the `toolUse` block the agent emitted, and
  2. a **user** message containing the matching **`toolResult`** (same `toolUseId`) with your result payload.
- The harness picks up exactly where it paused. Mismatched/missing `toolUseId` → the resume is rejected.

```python
# pause: first invoke ends with stopReason "tool_use" carrying a toolUse block
# resume: same session, echo the toolUse and supply the toolResult
messages = [
  {"role": "assistant", "content": [{"toolUse": {
      "toolUseId": tuid, "name": "request_human_login", "input": {...}}}]},
  {"role": "user", "content": [{"toolResult": {
      "toolUseId": tuid, "content": [{"text": "login complete"}]}}]},
]
client.invoke_harness(harnessArn=arn, runtimeSessionId=same_session_id, messages=messages, ...)
```

---

## Read-timeout

Turns that include long sleeps/waits (an S3 poll loop, a human-login pause) will blow past botocore's **default 60 s
read timeout**, which silently kills the stream mid-turn. Set a long read timeout on the data-plane client:

```python
from botocore.config import Config
client = boto3.client("bedrock-agentcore", region_name="us-east-1",
                      config=Config(read_timeout=1800, retries={"max_attempts": 0}))
```

1800 s (30 min) covers a realistic human-login delay plus poll intervals. Align it with the harness `timeoutSeconds`
(see `advanced-config.md`). Without this, the symptom is a stream that "just ends" after ~60 s with no error from the
agent.

---

## No-persist

**Browser sessions do NOT persist across separate `invoke_harness` turns.** Each new invoke turn re-initialises the
agent and a fresh browser session — the previous turn's logged-in cookies/page are gone. Therefore:

- Do the login **and** the work that depends on it **within a single invoke turn** (use the S3-signal or inline-function
  pause/resume *inside that turn* to wait for the human, rather than splitting login and work across two invokes).
- Don't expect to "log in on turn 1, use it on turn 2." Turn 2 starts cold.

---

## Retrieve-files

Files the agent writes to the **session filesystem** (e.g. `/mnt/reports/report.json`) live in the ephemeral microVM
and vanish when the session ends — there is no API to read the harness filesystem from outside. To get them out:

1. Grant the **execution role `s3:PutObject`** on a results bucket/prefix (extend `assets/iam_execution_role.json`).
2. Have the agent **upload** its output via the `shell` tool at end of run
   (`aws s3 cp /mnt/reports/report.json s3://bucket/results/`).
3. **Download** from S3 on your side after the invoke returns.

Bake the upload step into the system prompt / test-plan ("when finished, upload `/mnt/reports/*` to `s3://…`") so it
happens deterministically rather than relying on the agent to remember.
