"""finalize.py — assemble a summary.md per run + upload everything to S3."""
import glob
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

ROOT = os.environ.get("AGENTCORE_TESTS_ROOT", os.path.expanduser("~/agentcore-tests"))
RUN_TS = os.environ.get("AGENTCORE_TESTS_RUN")
BUCKET = "agentcore-tests-output-<ACCOUNT_ID>"

if not RUN_TS:
    runs = sorted(os.listdir(os.path.join(ROOT, "results")))
    RUN_TS = runs[-1] if runs else None
    print("no RUN_TS env, using latest:", RUN_TS)

if not RUN_TS:
    print("no run found"); sys.exit(1)

run_dir = os.path.join(ROOT, "results", RUN_TS)
log_dir = os.path.join(ROOT, "logs", RUN_TS)
ev_dir = os.path.join(ROOT, "evidence", RUN_TS)

print(f"finalizing run {RUN_TS}")
print(f"  run_dir: {run_dir}  -> {len(os.listdir(run_dir)) if os.path.exists(run_dir) else 0} json files")
print(f"  log_dir: {log_dir}")
print(f"  ev_dir : {ev_dir}")

results = []
for jf in sorted(glob.glob(os.path.join(run_dir, "*.json"))):
    try:
        d = json.load(open(jf))
        results.append(d)
    except Exception as e:
        print(f"WARN: cannot parse {jf}: {e}")

# summary.md
md = [f"# AgentCore e2e test run — {RUN_TS}\n"]
md.append("\n## Per-track summary\n\n| Track | Cases | Pass | Fail | Error | Duration (s) |\n|---|---|---|---|---|---|")
totals = {"cases": 0, "pass": 0, "fail": 0, "error": 0, "duration": 0.0}
for d in results:
    cases = d.get("cases", [])
    p = sum(1 for c in cases if c["status"] == "PASS")
    f_ = sum(1 for c in cases if c["status"] == "FAIL")
    er = sum(1 for c in cases if c["status"] == "ERROR")
    dur = round(sum(c.get("duration_s", 0) for c in cases), 2)
    md.append(f"| {d['track']} | {len(cases)} | {p} | {f_} | {er} | {dur} |")
    for k, v in [("cases", len(cases)), ("pass", p), ("fail", f_), ("error", er), ("duration", dur)]:
        totals[k] += v
md.append(f"| **TOTAL** | **{totals['cases']}** | **{totals['pass']}** | **{totals['fail']}** | **{totals['error']}** | **{round(totals['duration'],2)}** |")

md.append("\n## Per-case detail\n")
for d in results:
    md.append(f"\n### {d['track']}\n")
    md.append("| Case ID | Description | Status | Duration | Error |\n|---|---|---|---|---|")
    for c in d.get("cases", []):
        err = (c.get("error") or "").replace("|", "\\|").replace("\n", " ")[:120]
        md.append(f"| `{c['id']}` | {c['description']} | {c['status']} | {c['duration_s']}s | {err} |")

md.append(f"\n## Artifacts\n\n- structured results: `results/{RUN_TS}/*.json`\n- per-track logs: `logs/{RUN_TS}/*.log`\n- evidence files: `evidence/{RUN_TS}/<track>/...`\n")

summary = "\n".join(md)
sumpath = os.path.join(run_dir, "summary.md")
with open(sumpath, "w", encoding="utf-8") as f:
    f.write(summary)
print(f"wrote {sumpath} ({len(summary)} chars)")

# upload to S3
prefix = f"runs/{RUN_TS}"
print(f"\nuploading to s3://{BUCKET}/{prefix}/...")
for src, sub in [(run_dir, "results"), (log_dir, "logs"), (ev_dir, "evidence")]:
    if os.path.exists(src):
        cmd = ["aws", "s3", "sync", src, f"s3://{BUCKET}/{prefix}/{sub}", "--no-progress"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        print(f"  sync {sub}: {r.returncode} ({r.stdout.count(chr(10))} files)")

# also write a "latest" pointer
import json as _json
latest = {"latest_run": RUN_TS, "totals": totals, "tracks": [d["track"] for d in results]}
print(_json.dumps(latest, indent=2))
subprocess.run(["aws", "s3", "cp", "-",
                f"s3://{BUCKET}/runs/_LATEST.json"],
               input=_json.dumps(latest), text=True, capture_output=True)
print("done.")
