# AgentCore e2e test run — trackE2-20260614T154404Z


## Per-track summary

| Track | Cases | Pass | Fail | Error | Duration (s) |
|---|---|---|---|---|---|
| e2e-e2-codeinterp | 7 | 7 | 0 | 0 | 1.91 |
| **TOTAL** | **7** | **7** | **0** | **0** | **1.91** |

## Per-case detail


### e2e-e2-codeinterp

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `E2.1` | start_code_interpreter_session | PASS | 1.21s |  |
| `E2.2` | writeFiles — write a work file | PASS | 0.1s |  |
| `E2.3` | listFiles — file is present | PASS | 0.07s |  |
| `E2.4` | readFiles — content round-trips | PASS | 0.11s |  |
| `E2.5` | executeCommand — shell cat the file | PASS | 0.17s |  |
| `E2.6` | executeCode — python reads the same file (cross-tool persistence) | PASS | 0.14s |  |
| `E2.99` | stop_code_interpreter_session | PASS | 0.11s |  |

## Artifacts

- structured results: `results/trackE2-20260614T154404Z/*.json`
- per-track logs: `logs/trackE2-20260614T154404Z/*.log`
- evidence files: `evidence/trackE2-20260614T154404Z/<track>/...`
