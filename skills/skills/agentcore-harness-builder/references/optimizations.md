# Optimizations

AgentCore **Optimizations** (preview) improves an agent by generating better system prompts / tool descriptions and
validating them with A/B tests before deploying the winner.

## Important: console/preview-only right now

**Verified against boto3 1.43.29: there are ZERO control-plane operations** for Optimizations / Recommendations /
A/B tests. This feature is currently **console-driven (preview)**, not scriptable via the SDK. Do not write code
against guessed operation names — drive it from the console, and re-check the SDK as the preview evolves:

```bash
python -c "import boto3; ops=boto3.client('bedrock-agentcore-control',region_name='us-east-1').meta.service_model.operation_names; print([o for o in ops if any(k in o for k in ['Optimiz','Recommend','ABTest','Experiment'])])"
# currently prints []  -> confirm before scripting
```

## How it works (console flow)

1. **Recommendation** — generate improved **system prompts** or **tool descriptions** as code snippets or
   configuration bundles. This is the candidate change.
2. **Gateways with configuration bundle + rules** — override default configuration and define conditional execution.
3. **Gateway dynamic routing** — route traffic between configurations.
4. **Validate / A/B test** — compare a **control** vs a **variant**, view evaluation results, and **deploy the winning
   configuration bundle**.

## When to use it

After the harness is live and **Evaluations** (`evaluations.md`) show a weakness (missed evidence, over-escalation,
mis-classification, ambiguous tool descriptions). Create a recommendation targeting that dimension, A/B test control
vs variant on representative traffic, and deploy the winner only if it measurably beats control. This is the safe way
to change a production prompt — never replace a working config on a hunch.

## Data residency note

The console warns that Optimizations may transmit data across Regions within your geography for processing. Confirm
this is acceptable for your data classification before using it.

## Conceptual parallel

This mirrors how `skill-creator` optimizes a skill's *description* via a train/test loop — propose candidates, evaluate
on held-out cases, keep the winner. Here the target is the **deployed agent's** prompt/tool descriptions, validated on
agent traces.
