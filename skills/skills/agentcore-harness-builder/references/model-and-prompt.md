# Model & System Prompt

## Model configuration

The `model` field selects the provider and model. Verified shape (boto3 1.43.29) — the union has **four** provider
configs, and inference settings live **inside** the chosen config:

```json
"model": {
  "bedrockModelConfig": {
    "modelId": "global.anthropic.claude-sonnet-5",
    "apiFormat": "converse_stream",
    "maxTokens": 65536
  }
}
```

> **`temperature`/`topP` and Claude ≥ 4.7 (live-verified 2026-07):** Bedrock REJECTS `temperature`
> for Fable 5, Opus 5, Sonnet 5, Opus 4.8 and Opus 4.7 (`ValidationException: temperature is
> deprecated for this model`). The error surfaces only at FIRST INVOKE — CreateHarness and
> validate-config both accept the config, then every InvokeHarness dies with `runtimeClientError`.
> Omit `temperature`/`topP` for those models; Opus 4.6 / Sonnet 4.6 / Haiku 4.5 still accept them.

Provider union (pick exactly one):

| Config key | Required | Extra fields |
|---|---|---|
| `bedrockModelConfig` | `modelId` | `apiFormat`, `maxTokens`, `temperature`, `topP`, `additionalParams` |
| `openAiModelConfig` | `modelId`, `apiKeyArn` | `apiFormat`, `maxTokens`, `temperature`, `topP`, `additionalParams` |
| `geminiModelConfig` | `modelId`, `apiKeyArn` | `maxTokens`, `temperature`, `topP`, `topK` |
| `liteLlmModelConfig` | `modelId` | `apiKeyArn`, `apiBase`, `maxTokens`, `temperature`, `topP`, `additionalParams` |

The non-Bedrock providers store their key as a secret ARN (`apiKeyArn`) — wire it via an Identity credential provider
/ Token Vault (see `identity.md`), never inline. This is how a Harness does **multi-provider** switching.

### Choosing a model id

- **Prefer an inference profile id**, not a bare foundation-model id. Profiles route across regions for capacity and
  resilience:
  - `global.*` — global cross-region profile (e.g. `global.anthropic.claude-sonnet-5`)
  - `us.*` — US cross-region profile (e.g. `us.anthropic.claude-sonnet-5`)
- **Recommended default: `global.anthropic.claude-sonnet-5`** (live-confirmed available). For the hardest
  reasoning/agentic tasks, use `global.anthropic.claude-opus-5`. Older `claude-sonnet-4-6` still works as the
  service default but prefer the 5-series.
- A bare `anthropic.claude-...` id works but ties you to one region's capacity.
- The execution role must have `bedrock:InvokeModel` / Converse permissions for the chosen id (and the underlying
  foundation model the profile maps to).

### API format

Set `apiFormat` inside the model config. The enum (live-verified) is **`converse_stream`** / `responses` /
`chat_completions` — the old `CONVERSE` value is stale and rejected. Use **`converse_stream`** for Bedrock models:
the unified, provider-agnostic contract for messages, tool-use, and streaming. It's why `invoke_harness` takes
`messages=[{"role":"user","content":[{"text":"..."}]}]` and streams `contentBlockDelta` events. `responses` and
`chat_completions` route OpenAI-style formats via Bedrock Mantle.

### Multi-provider / per-invocation override

A Harness can switch providers (Bedrock → OpenAI → Gemini → LiteLLM) by using a different `*ModelConfig`, and can be
overridden per invocation without redeploying — a core reason to choose Harness over Runtime.

### Inference configuration

Temperature, top-p, and `maxTokens` live **inside** the model config (e.g. `model.bedrockModelConfig.maxTokens`), and
should align with the top-level `maxTokens` limit. For deterministic test/eval agents on models that still accept it
(Claude ≤ 4.6), set a low `temperature`; on Claude ≥ 4.7 omit it entirely (rejected — see the callout above) and
enforce determinism through the system prompt instead.

---

## System prompt

The `systemPrompt` field is a **list of content blocks**, not a bare string:

```json
"systemPrompt": [ { "text": "You are an expert QA tester for web applications. ..." } ]
```

### Writing a good harness system prompt

A Harness prompt should be **declarative and rule-based** because the harness runs the loop — you're specifying
behavior, not orchestration. Effective structure:

1. **Role** — one line: who the agent is and its domain.
2. **Job** — a numbered list of the steps it performs (navigate → interact → observe → compare → report).
3. **Rules** — hard constraints (stay on domain, never submit real PII, screenshot every FAIL, classify severity).
4. **Output contract** — exact artifacts and where to write them (e.g. JSON report to `/mnt/reports/...`, plus a
   human-readable summary). Be explicit; the harness has a persistent per-session filesystem.
5. **Reflection** (if memory is wired) — tell it to record patterns/learnings for future sessions.

Example (abridged, from a working UI-test harness):

```
You are an expert QA tester for web applications. Use the browser to navigate, click, type,
and verify UI behavior. Take screenshots as evidence. Report PASS/FAIL for each test case with
severity classification (CRITICAL/HIGH/MEDIUM/LOW).

Rules:
- Always screenshot before and after each significant action.
- Record console errors and network failures.
- Classify each case PASS / FAIL / BLOCKED / SKIPPED; include evidence for every FAIL.
- If blocked by a prior failure, mark BLOCKED and continue.
- Never navigate outside the target domain; never submit real PII or payment data.

Output the final report as JSON to /mnt/reports/test-report-latest.json and a Markdown summary
to /mnt/reports/summary.md.
```

Keep it focused. Long prompts cost tokens every turn; push reusable methodology into a **Skill**
(`references/skills.md`) rather than bloating the prompt.

### Prompt as an optimization target

The system prompt and tool descriptions are exactly what **Optimizations** (`references/optimizations.md`) generates
improved candidates for and A/B-tests. Write a clear first version, then let the optimization loop refine it against
real traces.
