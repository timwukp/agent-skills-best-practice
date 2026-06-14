# AgentCore e2e test run — 20260614T095338Z


## Per-track summary

| Track | Cases | Pass | Fail | Error | Duration (s) |
|---|---|---|---|---|---|
| e2e-0-validate-codeblocks | 1 | 1 | 0 | 0 | 0.85 |
| e2e-a-runtime | 4 | 3 | 0 | 1 | 46.72 |
| e2e-d-identity-registry | 5 | 5 | 0 | 0 | 0.85 |
| e2e-e-codeinterp | 4 | 4 | 0 | 0 | 1.6 |
| **TOTAL** | **14** | **13** | **0** | **1** | **50.02** |

## Per-case detail


### e2e-0-validate-codeblocks

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `0.1` | all reference code blocks parse + boto3 ops resolve + kwargs are valid params | PASS | 0.85s |  |

### e2e-a-runtime

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `A.1` | Create runtime via codeConfiguration (S3 source) + wait for READY | PASS | 15.77s |  |
| `A.2` | invoke_agent_runtime (data plane) — verify echo response | ERROR | 30.7s | RuntimeClientError: An error occurred (RuntimeClientError) when calling the InvokeAgentRuntime operation: Runtime initia |
| `A.3` | list_agent_runtime_endpoints — assert DEFAULT endpoint exists | PASS | 0.05s |  |
| `A.99` | Cleanup: delete runtime + source object | PASS | 0.2s |  |

### e2e-d-identity-registry

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `D.1` | CreateApiKeyCredentialProvider | PASS | 0.26s |  |
| `D.2` | GetApiKeyCredentialProvider — verify created | PASS | 0.05s |  |
| `D.3` | CreateRegistry | PASS | 0.16s |  |
| `D.4` | GetRegistry — verify created | PASS | 0.06s |  |
| `D.99` | Cleanup | PASS | 0.32s |  |

### e2e-e-codeinterp

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `E.1` | start_code_interpreter_session | PASS | 1.29s |  |
| `E.2` | invoke_code_interpreter — assert print(6*7) yields 42 | PASS | 0.16s |  |
| `E.3` | get_code_interpreter_session — alive | PASS | 0.04s |  |
| `E.99` | stop_code_interpreter_session — cleanup | PASS | 0.11s |  |

## Artifacts

- structured results: `results/20260614T095338Z/*.json`
- per-track logs: `logs/20260614T095338Z/*.log`
- evidence files: `evidence/20260614T095338Z/<track>/...`
