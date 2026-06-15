# AgentCore e2e test run — trackD2-20260614T153803Z


## Per-track summary

| Track | Cases | Pass | Fail | Error | Duration (s) |
|---|---|---|---|---|---|
| e2e-d2-identity-policy-registry | 4 | 4 | 0 | 0 | 77.47 |
| **TOTAL** | **4** | **4** | **0** | **0** | **77.47** |

## Per-case detail


### e2e-d2-identity-policy-registry

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `D2.1` | Workload Identity: create -> get -> delete | PASS | 0.19s |  |
| `D2.2` | Policy engine + Cedar policy: create -> get -> delete | PASS | 5.54s |  |
| `D2.3` | OAuth2 credential provider (GoogleOauth2): create -> get -> delete | PASS | 0.49s |  |
| `D2.4` | Registry record (AGENT_SKILLS inline): create registry + record -> get -> delete both | PASS | 71.25s |  |

## Artifacts

- structured results: `results/trackD2-20260614T153803Z/*.json`
- per-track logs: `logs/trackD2-20260614T153803Z/*.log`
- evidence files: `evidence/trackD2-20260614T153803Z/<track>/...`
