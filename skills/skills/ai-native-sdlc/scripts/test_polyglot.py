#!/usr/bin/env python3
"""test_polyglot.py — source-file detection across languages, and the deprecation path.

Two things are tested here because they are the same story.

POLYGLOT: coverage only applies to files the gate recognises as product source. Detection is
extension-based, so any language missing from the list is invisible: a C++ or Kotlin change
needs no plan, and the gate reports PASSED. That is a silent hole exactly where the tool
claims to be strict.

DEPRECATION: widening the list is a BREAKING change under this project's own policy in
COMPATIBILITY.md -- a .cpp file that needed no coverage yesterday needs it today, so a
previously-green repository turns red with no code change of its own. The policy says such a
change must ship as a WARNING in a MINOR release first, name its remediation, and only then
be enforced.

So the new languages are added as PENDING: they warn, they do not fail, and the warning names
the version that will enforce them. This file is the drill that proves the deprecation
mechanism works, rather than the policy being prose nobody has exercised.

Exit 0 = all pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE / "sdlc_ci_gate.py"
COMPAT = HERE.parent / "COMPATIBILITY.md"
BASE = "a" * 40

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def write(p: pathlib.Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(text.encode("utf-8"))


def make_repo(root: pathlib.Path, covered: list[str]) -> None:
    hdr = "- **Author:** A. Author\n- **Accepted-by:** B. Approver\n"
    d = root / "intent" / "feat"
    write(d / "intent.md", f"# i\n\n{hdr}- **Status:** accepted\n")
    write(d / "spec.md", f"# s\n\n{hdr}- **Status:** signed-off\n")
    listing = "".join(f"- `{f}`\n" for f in covered)
    write(d / "plan.md", f"# p\n\n{hdr}- **Accepted-for:** {BASE}\n"
         f"- **Status:** accepted\n\n## Files\n{listing}")
    write(root / ".sdlc" / "version", "1\n")
    write(root / ".sdlc" / "active", "feat\n")


def run_gate(root: pathlib.Path, changed: list[str]):
    listing = root / "_changed.txt"
    write(listing, "".join(f"{c}\n" for c in changed))
    p = subprocess.run(
        [sys.executable, str(GATE), "--repo", str(root),
         "--base-sha", BASE, "--changed-files-from", str(listing)],
        capture_output=True, text=True,
    )
    return p.returncode, p.stdout + p.stderr


# ------------------------------------------------------- already enforced
def test_enforced_languages() -> None:
    print("enforced languages must require plan coverage")
    for ext in (".py", ".js", ".ts", ".go", ".rs", ".java", ".rb", ".sh", ".sql"):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            f = f"src/app{ext}"
            write(root / f, "x\n")
            make_repo(root, ["src/other.py"])  # plan does NOT name f
            rc, out = run_gate(root, [f])
            check(f"{ext} uncovered is REFUSED", rc != 0, out.strip()[-120:])


# -------------------------------------------------------- promoted in v2
def test_promoted_languages() -> None:
    print("v2-promoted languages must require plan coverage")
    promoted = (".c", ".cpp", ".h", ".hpp", ".cs", ".kt", ".swift", ".php",
                ".scala", ".tf", ".vue", ".dart")
    for ext in promoted:
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            f = f"src/app{ext}"
            write(root / f, "x\n")
            make_repo(root, ["src/other.py"])
            rc, out = run_gate(root, [f])
            # v1 warned and passed under the announced deprecation window. v2 is
            # the promised enforcement release: the same uncovered file must fail.
            check(f"{ext} uncovered is REFUSED in v2", rc != 0,
                  f"exit={rc}: {out.strip()[-200:]}")
            check(f"{ext} refusal names the uncovered file", f in out,
                  f"got: {out.strip()[-220:]}")


def test_promoted_message_quality() -> None:
    print("the v2 coverage refusal must be actionable, not stale deprecation prose")
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        write(root / "src/a.cpp", "x\n")
        write(root / "src/b.kt", "y\n")
        make_repo(root, ["src/other.py"])
        rc, out = run_gate(root, ["src/a.cpp", "src/b.kt"])
        check("fails after the window", rc != 0, out.strip()[-180:])
        check("names the remediation (add them to the plan)", "plan.md" in out)
        check("lists every affected file", "src/a.cpp" in out and "src/b.kt" in out)
        check("does not claim enforcement is still in the future",
              "pass today" not in out.casefold() and "will be enforced" not in out.casefold(),
              f"got stale v1 prose: {out.strip()[-260:]}")
        # A covered promoted file must pass. It is now an ordinary enforced source
        # suffix, not a special warning category.
        make_repo(root, ["src/a.cpp", "src/b.kt"])
        rc2, out2 = run_gate(root, ["src/a.cpp", "src/b.kt"])
        check("covered promoted files pass", rc2 == 0,
              f"got: {out2.strip()[-220:]}")


def test_promoted_list_is_empty_and_documented() -> None:
    print("v2 policy hygiene")
    src = (HERE / "sdlc_ci_gate.py").read_text(encoding="utf-8")
    check("gate identifies as v2", "GATE_VERSION = 2" in src)

    import re as _re

    def extract(name: str) -> set[str]:
        m = _re.search(name + r"\s*=\s*\((.*?)\)", src, _re.DOTALL)
        return set(_re.findall(r'"([^"]+)"', m.group(1))) if m else set()

    enforced, pending = extract("SOURCE_SUFFIXES"), extract("PENDING_SOURCE_SUFFIXES")
    check("enforced list parsed", bool(enforced), f"enforced={len(enforced)}")
    check("v2 has no still-pending source suffixes", not pending,
          f"pending after the promised enforcement release: {sorted(pending)}")

    # The deprecation must be announced where adopters look, not only in code.
    compat = COMPAT.read_text(encoding="utf-8") if COMPAT.is_file() else ""
    check("COMPATIBILITY.md announces the pending enforcement", "sdlc-gate-v2" in compat,
          "a breaking change must be announced before it is enforced")
    for ext in sorted(pending)[:3]:
        check(f"COMPATIBILITY.md mentions {ext}", ext in compat)


def main() -> int:
    test_enforced_languages()
    test_promoted_languages()
    test_promoted_message_quality()
    test_promoted_list_is_empty_and_documented()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} -> {FAILURES}")
        return 1
    print("all polyglot tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
