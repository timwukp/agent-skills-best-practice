# AgentCore e2e test run — trackB-20260614T152541Z


## Per-track summary

| Track | Cases | Pass | Fail | Error | Duration (s) |
|---|---|---|---|---|---|
| e2e-b-gateway | 6 | 6 | 0 | 0 | 26.76 |
| **TOTAL** | **6** | **6** | **0** | **0** | **26.76** |

## Per-case detail


### e2e-b-gateway

| Case ID | Description | Status | Duration | Error |
|---|---|---|---|---|
| `B.1` | Ensure gateway execution role | PASS | 0.09s |  |
| `B.2` | create_gateway (MCP, AWS_IAM, SEMANTIC) + wait READY | PASS | 10.23s |  |
| `B.3` | create api-key provider + create_gateway_target (OpenAPI inline, API_KEY) + wait READY | PASS | 10.64s |  |
| `B.4` | create_gateway_rule routeToTarget — documents it requires an HTTP-protocol target (MCP targets are served directly) | PASS | 0.11s |  |
| `B.5` | get_gateway + list targets + list rules — verify | PASS | 0.13s |  |
| `B.99` | Cleanup: delete rule, target, gateway | PASS | 5.56s |  |

## Artifacts

- structured results: `results/trackB-20260614T152541Z/*.json`
- per-track logs: `logs/trackB-20260614T152541Z/*.log`
- evidence files: `evidence/trackB-20260614T152541Z/<track>/...`
