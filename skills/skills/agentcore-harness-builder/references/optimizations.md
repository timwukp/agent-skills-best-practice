# Optimizations

AgentCore **Optimizations** (preview) improves an agent by generating better system prompts / tool descriptions
(**Recommendations**), analyzing sessions (**Insights**), and validating changes with **A/B tests** before
deploying the winner.

## SDK support: DATA plane, not control plane

Earlier versions of this file said there were "ZERO control-plane operations" and the feature was console-only.
The first half is still true — the control plane has nothing — but the ops exist on the **data-plane client**
(`bedrock-agentcore`), verified live on boto3 1.43.51:

| Feature | Data-plane ops | Scriptable? |
|---|---|---|
| Recommendations | `StartRecommendation` / `GetRecommendation` / `ListRecommendations` / `DeleteRecommendation` | **Yes** (verified: created live) |
| A/B tests | `CreateABTest` / `GetABTest` / `ListABTests` / `UpdateABTest` / `DeleteABTest` | Yes — but `gatewayArn` is **required**: no Gateway front, no traffic split. Variants are configuration bundles (`bundleArn`+`bundleVersion`) or targets, with weights + per-variant online eval configs. Harnesses invoked directly (InvokeHarness) can't A/B natively — do serial compare + `UpdateHarness` instead |
| Insights | **fully scriptable via `CreateOnlineEvaluationConfig`** — the console's "Create insights" page is a wrapper over the same API: pass `insights` instead of `evaluators` | **Yes** (verified: created live, shows in console Insights tab) |

Always introspect **both** clients before declaring anything console-only:

```bash
python -c "import boto3; print([o for o in boto3.client('bedrock-agentcore-control',region_name='us-east-1').meta.service_model.operation_names if 'Recommend' in o or 'ABTest' in o])"
python -c "import boto3; print([o for o in boto3.client('bedrock-agentcore',region_name='us-east-1').meta.service_model.operation_names if 'Recommend' in o or 'ABTest' in o])"
```

## Insights — scriptable through CreateOnlineEvaluationConfig (verified live)

The console's Optimizations → "Create insights" page is a wrapper over the **online evaluation config** API.
An insights config is an online evaluation config that passes `insights` INSTEAD of `evaluators`
("Exactly one of evaluators or insights must be provided"):

```python
c = boto3.client("bedrock-agentcore-control", region_name=REGION)
c.create_online_evaluation_config(
    onlineEvaluationConfigName="ui_qa_insights",
    rule={"samplingConfig": {"samplingPercentage": 100.0}},
    dataSourceConfig={"cloudWatchLogs": {"logGroupNames": [...], "serviceNames": [...]}},
    insights=[{"insightId": "Builtin.Insight.FailureAnalysis"},
              {"insightId": "Builtin.Insight.UserIntent"},
              {"insightId": "Builtin.Insight.ExecutionSummary"}],
    clusteringConfig={"frequencies": ["DAILY"]},        # DAILY | WEEKLY | MONTHLY — report schedule
    evaluationExecutionRoleArn=eval_role_arn,
    enableOnCreate=True, clientToken=secrets.token_hex(20))
```

Valid Builtin insight IDs (from the service's own validation error): `Builtin.Insight.FailureAnalysis`,
`Builtin.Insight.UserIntent`, `Builtin.Insight.Explanation`, `Builtin.Insight.ExecutionSummary`.
The created config appears in the console under Optimizations → Insights, fully editable there.

**On-demand insight reports** (the console's "Create custom report") are `StartBatchEvaluation` with
`insights=` instead of `evaluators=` (same either/or rule). Results come back as **typed structures on
`GetBatchEvaluation`** — `failureAnalysisResult.failures[]` (clusters → subCategories → rootCauses),
`userIntentResult.userIntents[]`, `executionSummaryResult.executionSummaries[]` (approachTaken /
finalOutcome per session) — NOT in the output log group. Two gotchas: with
`dataSourceConfig.onlineEvaluationConfigSource` you must NOT pass `insights` (the config's own list is
used), and a time-range source can silently match 0 sessions — target explicit
`filterConfig.sessionIds` for deterministic reports. Scheduled (DAILY/WEEKLY/MONTHLY) reports from the
recurring config surface in the console's report list on their own cadence.

## StartRecommendation — working example (verified live)

```python
data = boto3.client("bedrock-agentcore", region_name=REGION)
r = data.start_recommendation(
    name="ui_qa_prompt_rec",
    type="SYSTEM_PROMPT_RECOMMENDATION",          # enum is NOT "SYSTEM_PROMPT"
    recommendationConfig={"systemPromptRecommendationConfig": {
        "systemPrompt": {"text": current_prompt},  # or a configurationBundle ref
        "agentTraces": {"cloudwatchLogs": {
            "logGroupArns": ["arn:aws:logs:...:log-group:/aws/bedrock-agentcore/runtimes/<runtime-id>-DEFAULT"],
            "serviceNames": ["harness_<Name>.DEFAULT"],
            "startTime": start, "endTime": end}},   # or sessionSpans / batchEvaluation source
        "evaluationConfig": {"evaluators": [        # MAX ONE evaluator (ValidationException on 2+)
            {"evaluatorArn": "arn:aws:bedrock-agentcore:::evaluator/Builtin.GoalSuccessRate"}]}}},
    clientToken=secrets.token_hex(20))
# poll data.get_recommendation(recommendationId=r["recommendationId"]) until COMPLETED
# result: recommendation.recommendationResult.systemPromptRecommendationResult
#   .recommendedSystemPrompt + .explanation
# NOTE list_recommendations() returns key "recommendationSummaries", not "recommendations"
```

Gotchas (all observed live):
- `type` enum: `SYSTEM_PROMPT_RECOMMENDATION` / `TOOL_DESCRIPTION_RECOMMENDATION` — not the console's shorter labels.
- `evaluationConfig.evaluators` max length **1**.
- `agentTraces` alternatives: `cloudwatchLogs` (log-group ARNs + serviceNames + time range), `sessionSpans`, or `batchEvaluation` (reuse a batch evaluation's traces via its ARN — composes with `evaluations.md`).
- Traces must contain **span documents** — set `OTEL_TRACES_SAMPLER=always_on` on the harness first (see `evaluations.md` prerequisite; without it every trace-consuming feature silently has nothing to read).

## A/B tests — full SDK anatomy

> **Verification level: shape-verified, NOT yet exercised end-to-end.** Everything in this section comes
> from SDK introspection cross-checked against the console wizard, plus one live probe (bundle `components`
> accepts arbitrary JSON — created and deleted). No Gateway, A/B test, or traffic split has been run for
> real yet; statistical results (`GetABTest.results`) are described from the output shape, not observed.
> The rest of this file (Recommendations, Insights, batch reports) IS verified end-to-end with live
> artifacts. Treat this section as a reliable map, not a tested route.

`CreateABTest` / `GetABTest` / `UpdateABTest` / `ListABTests` / `DeleteABTest` (data plane). A/B rides a
**Gateway**: creating one materializes a weighted Gateway *rule* that splits traffic.

**Two variant types** (console: "Select from configuration bundles" vs "Select from gateway targets"):

| Variant type | SDK field | What it compares |
|---|---|---|
| Configuration bundles | `variantConfiguration.configurationBundle {bundleArn, bundleVersion}` | two versioned config bundles (e.g. current vs recommended system prompt) applied over the same target |
| Gateway targets | `variantConfiguration.target {name}` | two gateway targets — **including two `agentcoreRuntime` endpoints**, i.e. two runtime/harness versions |

The target-type is the practical route for **harness** A/B: front the harness with a gateway
(`CreateGatewayTarget` → `targetConfiguration.http.agentcoreRuntime {arn, qualifier}`), register control and
variant runtimes as two targets, and let the A/B rule weight-route between them.

**Configuration bundles are git-like versioned JSON**: `components` is a **document-type map** (arbitrary
JSON values — verified live: `{"systemPrompt": {"configuration": {...}}}` accepted), with `branchName`,
`commitMessage`, version lineage (`parentVersionIds`). `StartRecommendation` can both *consume* a bundle
(`systemPrompt.configurationBundle` + `systemPromptJsonPath`) and *emit* one
(`recommendationResult.systemPromptRecommendationResult.configurationBundle`) — so the loop
Insights → Recommendation → bundle → A/B variant is fully scriptable.

**Results are a real stats engine** — `GetABTest.results.evaluatorMetrics[]` per evaluator:
`controlStats {sampleSize, mean}` vs `variantResults[] {mean, absoluteChange, percentChange, pValue,
confidenceInterval {lower, upper}, isSignificant}`. Deploy the winner by `UpdateABTest` re-weighting
(e.g. 0/100) or applying the winning bundle; `executionStatus` enum: NOT_STARTED / RUNNING / PAUSED / STOPPED.

Also on `CreateGatewayRule` directly (what A/B automates): `actions[].configurationBundle
.staticOverride|.weightedOverride {trafficSplit}` and `actions[].routeToTarget.staticRoute|.weightedRoute` —
plus `conditions[].matchPrincipals/matchPaths` for principal- or path-scoped rollouts (canary by caller).

## The full loop (console + SDK mix)

1. **Recommendation** — generate improved system prompts / tool descriptions (SDK or console).
2. **Gateways with configuration bundle + rules** — override default configuration, conditional execution.
3. **Gateway dynamic routing** — route traffic between configurations.
4. **A/B test** — control vs variant on live traffic (`CreateABTest` needs a `gatewayArn`; harnesses not fronted
   by a Gateway can't A/B natively — apply the winner via `UpdateHarness` instead), then deploy the winner.

## When to use it

After the harness is live and **Evaluations** (`evaluations.md`) show a weakness (missed evidence,
over-escalation, mis-classification, ambiguous tool descriptions). Create a recommendation targeting that
dimension, A/B test control vs variant on representative traffic, and deploy the winner only if it measurably
beats control. This is the safe way to change a production prompt — never replace a working config on a hunch.

## Data residency note

The console warns that Optimizations may transmit data across Regions within your geography for processing.
Confirm this is acceptable for your data classification before using it.

## Conceptual parallel

This mirrors how `skill-creator` optimizes a skill's *description* via a train/test loop — propose candidates,
evaluate on held-out cases, keep the winner. Here the target is the **deployed agent's** prompt/tool
descriptions, validated on agent traces.
