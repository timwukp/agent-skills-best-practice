#!/usr/bin/env python3
"""test_gate.py — feedback loop for sdlc_gate.py. Exit 0 = all pass, non-zero = fail."""
import subprocess
import sys
import tempfile
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE / "sdlc_gate.py"


def run(intent_dir, stage):
    r = subprocess.run([sys.executable, str(GATE), str(intent_dir), stage],
                       capture_output=True, text=True)
    return r.returncode


def write(d, name, status):
    (d / name).write_text(f"# X\n\n- **Status:** {status}\n", encoding="utf-8")


def main():
    fails = []
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)

        # 1. unfilled template placeholder must CLOSE the design gate
        write(d, "intent.md", "draft | accepted | rejected")
        if run(d, "design") != 2:
            fails.append("unfilled intent template should CLOSE design gate")

        # 2. draft intent must CLOSE design gate
        write(d, "intent.md", "draft")
        if run(d, "design") != 2:
            fails.append("draft intent should CLOSE design gate")

        # 3. accepted intent must OPEN design gate
        write(d, "intent.md", "accepted")
        if run(d, "design") != 0:
            fails.append("accepted intent should OPEN design gate")

        # 4. build needs BOTH accepted intent AND signed-off spec
        if run(d, "build") != 2:
            fails.append("build without spec should CLOSE")
        write(d, "spec.md", "signed-off")
        if run(d, "build") != 0:
            fails.append("accepted intent + signed-off spec should OPEN build")

        # 5. test stage needs accepted plan
        if run(d, "test") != 2:
            fails.append("test without plan should CLOSE")
        write(d, "plan.md", "accepted")
        if run(d, "test") != 0:
            fails.append("signed-off spec + accepted plan should OPEN test")

        # 6. missing artifact closes
        d2 = pathlib.Path(t) / "empty"
        d2.mkdir()
        if run(d2, "design") != 2:
            fails.append("missing intent should CLOSE design gate")

    # ---- gap coverage (added later, each proven by mutating the gate) --------
    with tempfile.TemporaryDirectory() as t:
        d = pathlib.Path(t)

        # 7. the 'deploy' stage was never exercised at all.
        write(d, "plan.md", "draft")
        if run(d, "deploy") != 2:
            fails.append("draft plan should CLOSE deploy gate")
        write(d, "plan.md", "accepted")
        if run(d, "deploy") != 0:
            fails.append("accepted plan should OPEN deploy gate")

        # 8. an unknown stage name must be refused, not silently treated as open.
        if run(d, "shipit") != 2:
            fails.append("unknown stage should exit 2")

        # 9. wrong argument count must be refused.
        r = subprocess.run([sys.executable, str(GATE)], capture_output=True, text=True)
        if r.returncode != 2:
            fails.append(f"no args should exit 2, got {r.returncode}")

        # 10. a file that exists but has NO Status line must close the gate,
        #     not be treated as satisfying it.
        (d / "intent.md").write_text("# title only, no status\n", encoding="utf-8")
        if run(d, "design") != 2:
            fails.append("intent with no Status line should CLOSE design gate")

        # 11. CASE VARIANCE. A human writing "Accepted" or "ACCEPTED" means the
        #     same thing as "accepted". If the gate is case-sensitive it blocks a
        #     correctly-accepted artifact forever, which is a silent false refusal.
        for variant in ("Accepted", "ACCEPTED", "accepted"):
            write(d, "intent.md", variant)
            if run(d, "design") != 0:
                fails.append(f"status '{variant}' should OPEN design gate (case-insensitive)")

        # 12. Trailing detail after the status word is still that status
        #     ("accepted by the product owner"), and must not be rejected.
        write(d, "intent.md", "accepted by the product owner 2026-09-02")
        if run(d, "design") != 0:
            fails.append("status with trailing detail should still OPEN the gate")

        # 13. A status that merely CONTAINS the word inside another word must not
        #     count: "unaccepted" / "not-accepted" are refusals, not acceptances.
        for bad in ("unaccepted", "not-accepted", "preaccepted"):
            write(d, "intent.md", bad)
            if run(d, "design") != 2:
                fails.append(f"status '{bad}' must NOT open the gate")

    if fails:
        print("FAIL:")
        for f in fails:
            print("  -", f)
        return 1
    print("all gate tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
