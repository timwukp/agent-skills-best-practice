# Versioning & Endpoints — Production Rollout / Rollback

Harness configurations are **immutably versioned**: `CreateHarness` produces version 1, and every `UpdateHarness`
creates a new version (the old one is untouched and still invocable). Named **endpoints** are pointers to versions —
they're how you separate "what production runs" from "what you're iterating on".

## The operations (live-verified on `bedrock-agentcore-control`)

| Op | What it does |
|---|---|
| `ListHarnessVersions` | List all immutable versions of a harness |
| `CreateHarnessEndpoint` | Create a named pointer (e.g. `prod`) to a specific version |
| `GetHarnessEndpoint` / `ListHarnessEndpoints` | Inspect endpoints and which version each targets |
| `UpdateHarnessEndpoint` | Repoint an endpoint to a different version (promote / roll back) |
| `DeleteHarnessEndpoint` | Remove an endpoint |

Every harness has a built-in **`DEFAULT`** endpoint that always tracks the **latest** version. If callers pass no
`qualifier`, they hit `DEFAULT` — meaning **every `UpdateHarness` immediately changes what they run**. Fine for dev;
not what you want for production.

## Qualifier on InvokeHarness

The data-plane `InvokeHarness` takes an optional **`qualifier`** — an endpoint name or a version number:

```python
data = boto3.client("bedrock-agentcore")
data.invoke_harness(harnessArn=ARN, qualifier="prod",          # or a specific version, e.g. "3"
                    runtimeSessionId=sid, messages=msgs)
```

```bash
python scripts/invoke_harness.py --harness-arn <ARN> --qualifier prod --prompt "..."
```

No `qualifier` → `DEFAULT` → latest version.

## Production rollout pattern

1. **Pin prod.** After the harness is verified (Phase 6), create the endpoint on the known-good version:
   ```python
   ctl.create_harness_endpoint(harnessId=HID, name="prod", version=N,
                               clientToken=secrets.token_hex(20))
   ```
   Production callers always pass `qualifier="prod"`.
2. **Iterate safely.** Keep changing config via `UpdateHarness` — each update creates a new version and moves only
   `DEFAULT`. Test the latest with no qualifier (or `qualifier="DEFAULT"`); prod traffic is untouched.
3. **Promote.** When the new version passes evaluation (Phase 7):
   ```python
   ctl.update_harness_endpoint(harnessId=HID, name="prod", version=N_new,
                               clientToken=secrets.token_hex(20))
   ```
4. **Roll back** = repoint: run the same `update_harness_endpoint` with the previous version number. Because
   versions are immutable, rollback is instant and exact — no config reconstruction.

Find version numbers with `ListHarnessVersions`; confirm what prod points at with
`GetHarnessEndpoint(harnessId=HID, name="prod")`.

## Practical notes

- `clientToken` ≥ 33 chars applies to the endpoint ops too (`secrets.token_hex(20)`).
- Stage more elaborately by adding endpoints (`staging`, `canary`) — each is just a named pointer; shift traffic by
  changing which qualifier your callers pass or by repointing the endpoint.
- Versions capture the **harness config** (model, prompt, tools, skills refs, limits). They do not freeze external
  resources the config points at (a git skill's default branch, a Gateway's targets) — those still float.
- Introspect when in doubt: `preflight.py --show-shape CreateHarnessEndpoint` / `UpdateHarnessEndpoint`.
