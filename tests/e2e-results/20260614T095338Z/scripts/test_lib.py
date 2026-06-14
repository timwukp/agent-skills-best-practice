"""Common test framework for AgentCore e2e tests on EC2.

Each test track imports `Runner`, registers test cases via `@case`, and calls `Runner.go()`.
A run produces:
  - results/<track>.json   : structured pass/fail per case + duration + evidence paths
  - logs/<track>.log       : stdout/stderr captured per case
  - evidence/<track>/...   : boto3 responses, raw output, etc.

All artifacts are uploaded to S3 at the end via finalize.py.
"""
import json
import os
import sys
import time
import traceback
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from io import StringIO

ROOT = os.environ.get("AGENTCORE_TESTS_ROOT", os.path.expanduser("~/agentcore-tests"))
RUN_TS = os.environ.get("AGENTCORE_TESTS_RUN", datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))


class Runner:
    def __init__(self, track: str):
        self.track = track
        self.cases = []
        self.results = []
        self.run_dir = os.path.join(ROOT, "results", RUN_TS)
        self.log_dir = os.path.join(ROOT, "logs", RUN_TS)
        self.evidence_dir = os.path.join(ROOT, "evidence", RUN_TS, track)
        for d in (self.run_dir, self.log_dir, self.evidence_dir):
            os.makedirs(d, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, f"{track}.log")
        self._log = open(self.log_file, "a", encoding="utf-8")
        self._log.write(f"\n\n========= {track} run {RUN_TS} =========\n")

    def case(self, case_id: str, description: str = ""):
        """Decorator: register a function as a test case. The function receives `evidence_dir`."""
        def deco(fn):
            self.cases.append({"id": case_id, "description": description or fn.__name__, "fn": fn})
            return fn
        return deco

    def _save_result(self, r):
        self.results.append(r)
        path = os.path.join(self.run_dir, f"{self.track}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"track": self.track, "run_ts": RUN_TS, "cases": self.results}, f, indent=2, default=str)

    def go(self):
        print(f"\n=== {self.track} : {len(self.cases)} cases @ {RUN_TS} ===")
        for c in self.cases:
            cid, desc, fn = c["id"], c["description"], c["fn"]
            print(f"\n--- {cid} : {desc} ---")
            self._log.write(f"\n--- {cid} : {desc} ---\n")
            buf_out, buf_err = StringIO(), StringIO()
            t0 = time.time()
            status, error = "PASS", None
            try:
                with redirect_stdout(buf_out), redirect_stderr(buf_err):
                    fn(evidence_dir=self.evidence_dir, case_id=cid)
            except AssertionError as e:
                status, error = "FAIL", f"AssertionError: {e}"
                traceback.print_exc(file=buf_err)
            except Exception as e:  # noqa: BLE001
                status, error = "ERROR", f"{type(e).__name__}: {e}"
                traceback.print_exc(file=buf_err)
            dt = round(time.time() - t0, 2)
            stdout, stderr = buf_out.getvalue(), buf_err.getvalue()
            self._log.write(f"[STATUS {status} duration {dt}s]\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n")
            self._log.flush()
            self._save_result({
                "id": cid, "description": desc, "status": status, "duration_s": dt,
                "error": error, "stdout_len": len(stdout), "stderr_len": len(stderr),
            })
            print(f"  {status} ({dt}s){' — ' + error if error else ''}")
        # final summary
        passes = sum(1 for r in self.results if r["status"] == "PASS")
        print(f"\n=== {self.track} summary: {passes}/{len(self.results)} passed ===")
        self._log.write(f"\n=== {self.track} summary: {passes}/{len(self.results)} passed ===\n")
        self._log.close()
        return self.results
