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
| A/B tests | `CreateABTest` / `GetABTest` / `ListABTests` / `UpdateABTest` / `DeleteABTest` | Yes (shape verified; targets a **Gateway** + variants + eval config) |
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
