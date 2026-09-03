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
    write(d / "plan.md", f"# p\n\n{hdr}- **Status:** accepted\n\n## Files\n{listing}")
    write(root / ".sdlc" / "version", "1\n")
    write(root / ".sdlc" / "active", "feat\n")


def run_gate(root: pathlib.Path, changed: list[str]):
    listing = root / "_changed.txt"
    write(listing, "".join(f"{c}\n" for c in changed))
    p = subprocess.run(
        [sys.executable, str(GATE), "--repo", str(root),
         "--changed-files-from", str(listing)],
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


# -------------------------------------------------------- pending (warn)
def test_pending_languages() -> None:
    print("pending languages must WARN, not fail (deprecation window)")
    # Languages a polyglot repo will actually contain, absent from the enforced list.
    pending = (".c", ".cpp", ".h", ".hpp", ".cs", ".kt", ".swift", ".php",
               ".scala", ".tf", ".vue", ".dart")
    for ext in pending:
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            f = f"src/app{ext}"
            write(root / f, "x\n")
            make_repo(root, ["src/other.py"])
            rc, out = run_gate(root, [f])
            # Must NOT fail -- that is the whole point of a deprecation window.
            check(f"{ext} uncovered does not fail the build yet", rc == 0,
                  f"exit={rc}: {out.strip()[-160:]}")
            # But it must be visible, and must say it will be enforced.
            check(f"{ext} produces a deprecation warning", ext in out and "will be enforced" in out,
                  f"got: {out.strip()[-200:]}")


def test_warning_quality() -> None:
    print("the deprecation warning must be actionable")
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        write(root / "src/a.cpp", "x\n")
        write(root / "src/b.kt", "y\n")
        make_repo(root, ["src/other.py"])
        rc, out = run_gate(root, ["src/a.cpp", "src/b.kt"])
        check("passes during the window", rc == 0, out.strip()[-160:])
        check("names the version that will enforce", "sdlc-gate-v2" in out,
              f"got: {out.strip()[-250:]}")
        check("names the remediation (add them to the plan)", "plan.md" in out)
        check("lists every affected file", "src/a.cpp" in out and "src/b.kt" in out)
        # A covered pending file must NOT warn: the warning is about MISSING coverage,
        # not about the extension existing.
        make_repo(root, ["src/a.cpp", "src/b.kt"])
        rc2, out2 = run_gate(root, ["src/a.cpp", "src/b.kt"])
        check("no warning once the plan names them", rc2 == 0 and "will be enforced" not in out2,
              f"got: {out2.strip()[-200:]}")


def test_no_overlap_and_documented() -> None:
    print("policy hygiene")
    src = (HERE / "sdlc_ci_gate.py").read_text(encoding="utf-8")
    check("PENDING_SOURCE_SUFFIXES exists", "PENDING_SOURCE_SUFFIXES" in src)
    # An extension in both lists would be enforced and warned simultaneously -- incoherent.
    import re as _re

    def extract(name: str) -> set[str]:
        m = _re.search(name + r"\s*=\s*\((.*?)\)", src, _re.DOTALL)
        return set(_re.findall(r'"([^"]+)"', m.group(1))) if m else set()

    enforced, pending = extract("SOURCE_SUFFIXES"), extract("PENDING_SOURCE_SUFFIXES")
    check("both lists parsed", bool(enforced) and bool(pending),
          f"enforced={len(enforced)} pending={len(pending)}")
    overlap = enforced & pending
    check("no suffix is both enforced and pending", not overlap, f"overlap: {overlap}")

    # The deprecation must be announced where adopters look, not only in code.
    compat = COMPAT.read_text(encoding="utf-8") if COMPAT.is_file() else ""
    check("COMPATIBILITY.md announces the pending enforcement", "sdlc-gate-v2" in compat,
          "a breaking change must be announced before it is enforced")
    for ext in sorted(pending)[:3]:
        check(f"COMPATIBILITY.md mentions {ext}", ext in compat)


def main() -> int:
    test_enforced_languages()
    test_pending_languages()
    test_warning_quality()
    test_no_overlap_and_documented()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} -> {FAILURES}")
        return 1
    print("all polyglot tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
