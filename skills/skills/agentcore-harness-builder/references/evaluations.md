# Evaluations

AgentCore **Evaluations** (preview) scores agent behavior from its traces. The control-plane SDK exposes an **online
evaluation configuration** API (verified in boto3 1.43.29); **batch evaluation** and **custom evaluators** are surfaced
in the console and may not yet have dedicated SDK operations — introspect before assuming.

## What's in the SDK (verified)

`CreateOnlineEvaluationConfig` / `GetOnlineEvaluationConfig` / `ListOnlineEvaluationConfigs` /
`UpdateOnlineEvaluationConfig` / `DeleteOnlineEvaluationConfig`.

`CreateOnlineEvaluationConfig` input shape:

| Field | Type | Notes |
|---|---|---|
| `onlineEvaluationConfigName` | string **[req]** | Name of the config. |
| `rule` | structure **[req]** | `{samplingConfig [req], filters, sessionConfig}` — what traffic to evaluate and how to sample. |
| `dataSourceConfig` | structure **[req]** | `{cloudWatchLogs: {...}}` — where traces come from (ties into `observability.md`). |
| `evaluators` | list | Which evaluators to run. |
| `insights` | list | Insight configs. |
| `clusteringConfig` | structure | `{frequencies [req]}` for clustering results. |
| `evaluationExecutionRoleArn` | string **[req]** | Role used to read traces / write results. |
| `enableOnCreate` | boolean **[req]** | Start scoring immediately. |
| `tags` | map | Standard tags. |

```python
c.create_online_evaluation_config(
    onlineEvaluationConfigName="ui-test-quality",
    rule={"samplingConfig": {...}, "filters": [...]},
    dataSourceConfig={"cloudWatchLogs": {...}},
    evaluators=[...],
    evaluationExecutionRoleArn=eval_role_arn,
    enableOnCreate=True,
)
```

## How it fits the workflow

1. Wire **observability first** — traces must exist in CloudWatch Logs for `dataSourceConfig.cloudWatchLogs` to read.
2. Create an online evaluation config that samples live traffic, runs evaluators, and writes scores.
3. **Results surface in AgentCore Observability** — view them on the CloudWatch Observability page for the agent.
4. Use the scores to drive **Optimizations** (`optimizations.md`): identify the weak dimension, propose a fix, A/B
   test it.

## Batch evaluation & custom evaluators (console)

The console also offers **batch evaluation** (score a set of captured traces offline and Compare across variations) and
**custom evaluators** (your own scoring logic for domain-specific criteria — e.g. for a UI-test agent:
evidence-completeness, severity-classification accuracy, false-positive rate). If you need these programmatically,
introspect for any newer ops first:
```bash
python scripts/preflight.py --show-shape CreateOnlineEvaluationConfig
python -c "import boto3;print([o for o in boto3.client('bedrock-agentcore-control',region_name='us-east-1').meta.service_model.operation_names if 'Eval' in o])"
```

## Layering note

Distinguish these from the *skill-creator* eval loop used to build this Kiro skill: that tests whether **this skill**
produces good harness configs; AgentCore Evaluations test whether the **deployed harness agent** behaves well at
runtime.
