#!/usr/bin/env python3
"""test_ci_gate.py — tests for sdlc_ci_gate.py.

This component previously had NO test file at all; it was only exercised by
throwaway shell commands. Written before fixing the gaps it exposes.

The gate's contract: exit 0 = chain valid, exit 1 = violation. It fails CLOSED,
so a false PASS is the dangerous direction and most cases here assert refusal.

Exit 0 = all pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

GATE = pathlib.Path(__file__).resolve().parent / "sdlc_ci_gate.py"
PASS, VIOLATION = 0, 1


def run(repo: pathlib.Path, *extra: str) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, str(GATE), "--repo", str(repo), *extra],
        capture_output=True, text=True,
    )
    return p.returncode, p.stdout + p.stderr


def mk(root: pathlib.Path, slug: str, **statuses: str) -> pathlib.Path:
    d = root / "intent" / slug
    d.mkdir(parents=True, exist_ok=True)
    for name, st in statuses.items():
        # Author / Accepted-by are required on any artifact claiming approval
        # (separation of duties). Distinct names here so these cases exercise what
        # they are actually about rather than tripping the duties check.
        (d / f"{name}.md").write_text(
            f"# {name}\n\n- **Author:** alice\n- **Accepted-by:** bob\n"
            f"- **Status:** {st}\n",
            encoding="utf-8",
        )
    return d


def changed(root: pathlib.Path, *paths: str) -> str:
    f = root / "changed.txt"
    f.write_text("\n".join(paths) + "\n", encoding="utf-8")
    return str(f)


def main() -> int:
    fails: list[str] = []

    def check(label: str, got: int, want: int, out: str = "") -> None:
        if got != want:
            fails.append(f"{label}: exit {got}, want {want} :: {out.strip()[:200]}")

    # 1. Fully accepted chain + source change -> PASS.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="signed-off", plan="accepted")
        code, out = run(r, "--changed-files-from", changed(r, "src/a.py"))
        check("accepted chain passes", code, PASS, out)

    # 2. Skipped stage (plan accepted, spec draft) -> VIOLATION.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="draft", plan="accepted")
        code, out = run(r, "--changed-files-from", changed(r, "src/a.py"))
        check("skipped stage is a violation", code, VIOLATION, out)

    # 3. Unfilled template placeholder -> VIOLATION.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="draft | accepted | rejected")
        code, out = run(r)
        check("template placeholder is a violation", code, VIOLATION, out)

    # 4. Only meta files changed, nothing accepted -> PASS.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="draft")
        code, out = run(r, "--changed-files-from",
                        changed(r, "README.md", "intent/feat/intent.md", "evals/check_a.py",
                                ".github/workflows/x.yml", "docs/guide.md"))
        check("meta-only change passes", code, PASS, out)

    # ---- gaps this file was written to expose --------------------------------

    # 5. CASE AND TRAILING DETAIL must be honoured the same way the LOCAL gate
    #    honours them, or a repo passes one gate and fails the other.
    for variant in ("Accepted", "ACCEPTED", "accepted by the product owner"):
        with tempfile.TemporaryDirectory() as t:
            r = pathlib.Path(t)
            mk(r, "feat", intent=variant, spec="signed-off", plan="accepted")
            code, out = run(r, "--changed-files-from", changed(r, "src/a.py"))
            check(f"intent status '{variant}' should pass", code, PASS, out)

    # 6. A refusal that merely CONTAINS the word must never pass.
    for bad in ("not-accepted", "unaccepted"):
        with tempfile.TemporaryDirectory() as t:
            r = pathlib.Path(t)
            mk(r, "feat", intent=bad, spec="signed-off", plan="accepted")
            code, out = run(r, "--changed-files-from", changed(r, "src/a.py"))
            check(f"intent status '{bad}' must be a violation", code, VIOLATION, out)

    # 7. Two slugs, only one complete: a source change is covered by the complete
    #    one, so this passes — but the incomplete one must not itself be an error
    #    merely for being in progress.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "done", intent="accepted", spec="signed-off", plan="accepted")
        mk(r, "wip", intent="draft")
        code, out = run(r, "--changed-files-from", changed(r, "src/a.py"))
        check("one complete slug covers the change", code, PASS, out)

    # 8. --require-active: missing pointer file is a violation.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="signed-off", plan="accepted")
        code, out = run(r, "--require-active")
        check("missing .sdlc/active violates --require-active", code, VIOLATION, out)

    # 9. --require-active: pointer naming a nonexistent slug is a violation.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="signed-off", plan="accepted")
        (r / ".sdlc").mkdir(parents=True, exist_ok=True)
        (r / ".sdlc" / "active").write_text("ghost\n", encoding="utf-8")
        code, out = run(r, "--require-active")
        check("active naming a ghost slug violates", code, VIOLATION, out)

    # 10. --require-active satisfied.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="signed-off", plan="accepted")
        (r / ".sdlc").mkdir(parents=True, exist_ok=True)
        (r / ".sdlc" / "active").write_text("feat\n", encoding="utf-8")
        code, out = run(r, "--require-active")
        check("valid active passes", code, PASS, out)

    # 11. intent.md missing entirely from a slug dir -> VIOLATION.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", spec="signed-off")
        code, out = run(r)
        check("slug without intent.md violates", code, VIOLATION, out)

    # 12. A nonexistent changed-files list must be a VIOLATION, not silently
    #     skipped — otherwise a CI misconfiguration disables the coverage check.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="signed-off", plan="accepted")
        code, out = run(r, "--changed-files-from", str(r / "nope.txt"))
        check("missing changed-files list violates", code, VIOLATION, out)

    # 13. No intent/ directory at all and no source change: nothing to enforce.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        code, out = run(r)
        check("repo not using the chain passes", code, PASS, out)

    # 14. ...but a SOURCE change with no intent/ at all must be a violation.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        code, out = run(r, "--changed-files-from", changed(r, "src/a.py"))
        check("source change with no chain violates", code, VIOLATION, out)

    # 15. LADDER IN ISOLATION. Cases 2 and 11 above also trip the source-coverage
    #     check, so they stay red even if the ladder checks are deleted. These pass
    #     NO changed-files list, so the ladder is the only thing that can fail.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="draft", spec="signed-off")
        code, out = run(r)
        check("spec signed-off over a draft intent violates on its own", code, VIOLATION, out)

    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", intent="accepted", spec="draft", plan="accepted")
        code, out = run(r)
        check("plan accepted over a draft spec violates on its own", code, VIOLATION, out)

    # 16. MISSING intent.md IN ISOLATION. Case 11 also trips the ladder (spec
    #     signed-off with no intent). Here the spec is a draft, so nothing but the
    #     missing-intent.md rule can fail.
    with tempfile.TemporaryDirectory() as t:
        r = pathlib.Path(t)
        mk(r, "feat", spec="draft")
        code, out = run(r)
        check("slug missing intent.md violates on its own", code, VIOLATION, out)

    # 17. CONSISTENCY: sdlc_gate.py and sdlc_ci_gate.py each carry their own copy
    #     of the status matcher, because the CI gate is vendored into repos and
    #     must run with no imports. If the copies drift, a repo passes one gate and
    #     fails the other. Assert they agree on the same table.
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    try:
        import importlib

        local = importlib.import_module("sdlc_gate")
        ci = importlib.import_module("sdlc_ci_gate")
    except Exception as exc:  # pragma: no cover - import failure is itself a fail
        fails.append(f"could not import both gates for the consistency check: {exc}")
    else:
        table = [
            ("accepted", "accepted", True),
            ("Accepted", "accepted", True),
            ("ACCEPTED", "accepted", True),
            ("accepted by the product owner", "accepted", True),
            ("not-accepted", "accepted", False),
            ("unaccepted", "accepted", False),
            ("preaccepted", "accepted", False),
            ("draft", "accepted", False),
            ("signed-off", "signed-off", True),
            ("Signed-Off", "signed-off", True),
            ("signed off", "signed-off", False),
            ("<missing>", "accepted", False),
            ("<unset-template>", "accepted", False),
            ("<no-status>", "accepted", False),
        ]
        for status, needed, want in table:
            a = local.status_satisfies(status, needed)
            b = ci.satisfies(status, needed)
            if a != b:
                fails.append(
                    f"matchers DISAGREE on ('{status}','{needed}'): "
                    f"sdlc_gate={a} sdlc_ci_gate={b}"
                )
            elif a != want:
                fails.append(
                    f"both matchers wrong on ('{status}','{needed}'): got {a}, want {want}"
                )

    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        return 1
    print("all CI gate tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
