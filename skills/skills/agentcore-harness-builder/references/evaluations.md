# Evaluations

AgentCore **Evaluations** (preview) scores agent behavior from its traces. There are TWO surfaces, on TWO
different SDK clients — introspect both before assuming anything is console-only:

- **Online evaluation configs** — control plane (`bedrock-agentcore-control`): continuous scoring of live traffic.
- **Batch evaluations** — **data plane (`bedrock-agentcore`)**: on-demand offline scoring of historical sessions.
  Earlier versions of this file said batch had no SDK — wrong; the ops were on the other client.

## PREREQUISITE: turn trace sampling ON (or nothing will ever score)

Harness runtimes default to `trace_sampled=False`. Evaluators do **not** read the raw DEFAULT log-group
lines — they read **structured OTel spans** (via CloudWatch Transaction Search → the account `aws/spans`
log group). With sampling off (the default):

- an online evaluation config sits ACTIVE/ENABLED **forever with zero scores and zero errors**;
- a batch evaluation FAILS with `All N sessions failed` even though the sessions clearly exist.

Fix — one env var on the harness (verified live: spans appear and evaluations score immediately after):

```python
ctl.update_harness(harnessId=HID,
    environmentVariables={"OTEL_TRACES_SAMPLER": "always_on"},
    clientToken=secrets.token_hex(20))
```

Also confirm Transaction Search is active (`xray get-trace-segment-destination` → `CloudWatchLogs/ACTIVE`).

## Online evaluation configs (control plane — verified)

`CreateOnlineEvaluationConfig` / `GetOnlineEvaluationConfig` / `ListOnlineEvaluationConfigs` /
`UpdateOnlineEvaluationConfig` / `DeleteOnlineEvaluationConfig`, plus `CreateEvaluator` etc. for custom
evaluators. **16 Builtin evaluators ship ready to reference** (`list_evaluators()`): Correctness,
GoalSuccessRate, ToolSelectionAccuracy, Helpfulness, Faithfulness, the Trajectory* family, and more —
prefer them over building custom ones.

```python
c = boto3.client("bedrock-agentcore-control", region_name=REGION)
c.create_online_evaluation_config(
    onlineEvaluationConfigName="ui_qa_harness_quality",   # regex [a-zA-Z][a-zA-Z0-9_]{0,47} — NO dashes
    rule={"samplingConfig": {"samplingPercentage": 100.0}},
    dataSourceConfig={"cloudWatchLogs": {
        "logGroupNames": ["/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT"],
        "serviceNames": ["harness_<Name>.DEFAULT"]}},      # must match the span resource service.name
    evaluators=[{"evaluatorId": "Builtin.Correctness"},
                {"evaluatorId": "Builtin.GoalSuccessRate"},
                {"evaluatorId": "Builtin.ToolSelectionAccuracy"}],
    evaluationExecutionRoleArn=eval_role_arn,
    enableOnCreate=True,
    clientToken=secrets.token_hex(20))                     # clientToken min length 33 — token_hex(16) FAILS
```

Validation gotchas (all observed live):

| Field | Gotcha |
|---|---|
| `onlineEvaluationConfigName` | `[a-zA-Z][a-zA-Z0-9_]{0,47}` — dashes rejected |
| `clientToken` | min length **33** — use `secrets.token_hex(20)` |
| `evaluationExecutionRoleArn` | validated **server-side at create** against the log groups; scope-limited log ARNs can fail — grant broad logs read |

Results land in `/aws/bedrock-agentcore/evaluations/results/<config-id>` (log group auto-created) and
surface in CloudWatch → AgentCore Observability. Online scoring is **asynchronous batch-cadence** — expect
minutes-to-hours of lag; do not diagnose "broken" from lag alone (diagnose from missing spans instead).

## Batch evaluations (DATA plane — verified, was wrongly assumed console-only)

On `bedrock-agentcore` (the data-plane client): `StartBatchEvaluation` / `GetBatchEvaluation` /
`ListBatchEvaluations` / `StopBatchEvaluation` / `DeleteBatchEvaluation`. Scores historical sessions in
**minutes** — the fast path when you can't wait for the online cadence (demos, CI gates):

```python
data = boto3.client("bedrock-agentcore", region_name=REGION)
r = data.start_batch_evaluation(
    batchEvaluationName="ui_qa_batch",
    evaluators=[{"evaluatorId": "Builtin.Correctness"},
                {"evaluatorId": "Builtin.GoalSuccessRate"},
                {"evaluatorId": "Builtin.ToolSelectionAccuracy"}],
    dataSourceConfig={"cloudWatchLogs": {
        "serviceNames": ["harness_<Name>.DEFAULT"],
        "logGroupNames": ["/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT"],
        "filterConfig": {"sessionIds": ["<runtimeSessionId>", ...]}}},   # or timeRange
    clientToken=secrets.token_hex(20))
# poll: data.get_batch_evaluation(batchEvaluationId=r["batchEvaluationId"])
# → evaluationResults.evaluatorSummaries[].statistics.averageScore
```

`dataSourceConfig` alternatives: `onlineEvaluationConfigSource` (reuse an online config's source +
`timeRange`) instead of raw `cloudWatchLogs`. A job evaluates up to 500 sessions, up to 10 evaluators.
Statuses: PENDING → IN_PROGRESS → COMPLETED / COMPLETED_WITH_ERRORS / FAILED. Aggregate results are in the
Get response; per-session details go to
`/aws/bedrock-agentcore/evaluations/batch-evaluations/results/default` (stream `run-<id>`).

IAM for the caller — `StartBatchEvaluation` uses **FAS** (forward-access sessions): the service performs
several actions with the CALLER's credentials, so the caller needs more than the obvious three
(`bedrock-agentcore:StartBatchEvaluation` / `GetBatchEvaluation` / `ListBatchEvaluations`), all observed live:

- `logs:DescribeLogGroups` on **`Resource: "*"`** — a scoped log-group ARN fails the service's verification
  ("Cannot verify log group … ensure the execution role has logs:DescribeLogGroups").
- `logs:PutRetentionPolicy` + `logs:CreateLogGroup` — the service creates the results log group with the
  caller's credentials ("FAS credentials do not have permission to set log group retention policy").
- read access to the account `aws/spans` log group (Transaction Search destination) — evaluators read span
  documents from there, and per-session failures report "log events but no span documents" otherwise.

Two more operational gotchas:
- `batchEvaluationName` is **account-unique forever** — a completed job still holds its name
  (ConflictException on reuse); suffix names with a random token.
- Sessions that ran **before** `OTEL_TRACES_SAMPLER=always_on` was set can never be scored (no span
  documents exist) — filter them out of `sessionIds`, or the job lands in COMPLETED_WITH_ERRORS/FAILED.

## How it fits the workflow

1. Wire **observability** (`observability.md`) AND set `OTEL_TRACES_SAMPLER=always_on` — spans must exist first.
2. Create an **online evaluation config** for continuous scoring of live traffic.
3. Need scores NOW (demo, CI gate)? Run a **batch evaluation** over recent sessions — minutes, not hours.
4. Use the scores to drive **Optimizations** (`optimizations.md`): identify the weak dimension, propose a fix,
   A/B test it.

Re-introspect both clients as the preview evolves:
```bash
python -c "import boto3; print([o for o in boto3.client('bedrock-agentcore-control',region_name='us-east-1').meta.service_model.operation_names if 'Eval' in o])"
python -c "import boto3; print([o for o in boto3.client('bedrock-agentcore',region_name='us-east-1').meta.service_model.operation_names if 'valuat' in o])"
```

## Layering note

Distinguish these from the *skill-creator* eval loop used to build this Kiro skill: that tests whether **this
skill** produces good harness configs; AgentCore Evaluations test whether the **deployed harness agent**
behaves well at runtime.
