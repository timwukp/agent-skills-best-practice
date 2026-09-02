#!/usr/bin/env python3
"""test_support_matrix.py — the documented support matrix must match what CI actually runs.

WHY THIS EXISTS: the repeated defect in this project has not been broken code, it has been
documents claiming more than reality. Concrete instances already found by hand:

  * COMPATIBILITY.md claimed "Python 3.12 (CI)" while the workflow pinned 3.11.
  * limitations.md initially marked two gaps "fixed" that were never implemented.
  * SECURITY.md pointed users at Private Vulnerability Reporting while the setting was OFF.

A prose table cannot be trusted to stay true, so this test makes documentation drift a
BUILD FAILURE. COMPATIBILITY.md carries a machine-readable `support-matrix` JSON block as
the single source of truth; the prose table must agree with it, and CI must actually cover
everything the block claims is verified.

Claiming LESS than CI covers is fine (under-promising). Claiming MORE is a failure.
"""

from __future__ import annotations

import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
COMPAT = SKILL / "COMPATIBILITY.md"

FAILURES: list[str] = []
SKIPS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def find_repo_root() -> pathlib.Path | None:
    """Walk up looking for .github/workflows. Absent when the skill is installed standalone."""
    for parent in [SKILL, *SKILL.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    return None


def extract_matrix_block(text: str) -> dict | None:
    """Read the fenced ```json support-matrix block."""
    m = re.search(r"```json\s+support-matrix\s*\n(.*?)\n```", text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        FAILURES.append(f"support-matrix block is not valid JSON: {exc}")
        return None


def ci_coverage(root: pathlib.Path) -> tuple[set[str], set[str]]:
    """Collect every runs-on image and python-version appearing in the repo's workflows.

    Deliberately a plain text scan rather than a YAML parse: GitHub matrix expressions like
    ${{ matrix.os }} are not resolvable statically, so the literal values declared in the
    matrix lists are what we compare against.
    """
    runners: set[str] = set()
    pythons: set[str] = set()
    for wf in sorted((root / ".github" / "workflows").glob("*.yml")):
        text = wf.read_text(encoding="utf-8")
        for mo in re.finditer(r"runs-on:\s*\[?([^\]\n]+)\]?", text):
            for tok in mo.group(1).split(","):
                tok = tok.strip().strip("\"'")
                if tok and not tok.startswith("${{"):
                    runners.add(tok)
        # Matrix list form:  os: [ubuntu-latest, windows-latest]
        for mo in re.finditer(r"^\s*os:\s*\[([^\]]+)\]", text, re.MULTILINE):
            for tok in mo.group(1).split(","):
                runners.add(tok.strip().strip("\"'"))
        for mo in re.finditer(r"python-version:\s*\[([^\]]+)\]", text):
            for tok in mo.group(1).split(","):
                pythons.add(tok.strip().strip("\"'"))
        for mo in re.finditer(r"python-version:\s*[\"']?([0-9]+\.[0-9]+)[\"']?\s*$", text, re.MULTILINE):
            pythons.add(mo.group(1))
    return runners, pythons


def main() -> int:
    print("support matrix <-> CI consistency")

    if not COMPAT.is_file():
        print(f"  FAIL COMPATIBILITY.md not found at {COMPAT}")
        return 1
    text = COMPAT.read_text(encoding="utf-8")

    block = extract_matrix_block(text)
    check(
        "COMPATIBILITY.md carries a machine-readable support-matrix block",
        block is not None,
        "no ```json support-matrix fenced block found — prose alone cannot be verified",
    )
    if block is None:
        print(f"\nFAILED: {len(FAILURES)} -> {FAILURES}")
        return 1

    # --- shape of the declaration -------------------------------------------------
    for key in ("ci_verified", "documented_untested"):
        check(f"block declares '{key}'", key in block, f"keys present: {sorted(block)}")
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} -> {FAILURES}")
        return 1

    verified = block["ci_verified"]
    for key in ("os", "python"):
        check(f"ci_verified declares '{key}'", key in verified,
              f"keys present: {sorted(verified)}")
    if FAILURES:
        print(f"\nFAILED: {len(FAILURES)} -> {FAILURES}")
        return 1

    check("ci_verified.os is non-empty", bool(verified["os"]))
    check("ci_verified.python is non-empty", bool(verified["python"]))

    # --- the prose table must not contradict the block ----------------------------
    # Every value claimed verified must literally appear in the document body, so the
    # human-readable table cannot silently drift from the machine-readable claim.
    for os_name in verified["os"]:
        check(f"prose mentions verified OS '{os_name}'", os_name in text)
    for py in verified["python"]:
        check(f"prose mentions verified Python '{py}'", py in text)

    # A value cannot be both verified and untested — that is a self-contradiction.
    untested = block["documented_untested"]
    overlap_os = set(verified["os"]) & set(untested.get("os", []))
    check("no OS is both verified and untested", not overlap_os, f"overlap: {overlap_os}")
    overlap_py = set(verified["python"]) & set(untested.get("python", []))
    check("no Python is both verified and untested", not overlap_py, f"overlap: {overlap_py}")

    # --- CI must actually cover every verified claim -------------------------------
    root = find_repo_root()
    if root is None:
        msg = ("CI cross-check SKIPPED — no .github/workflows above the skill "
               "(expected when installed standalone; MUST run in the source repo)")
        print(f"  SKIP {msg}")
        SKIPS.append(msg)
    else:
        runners, pythons = ci_coverage(root)
        print(f"  (CI declares runners={sorted(runners)} pythons={sorted(pythons)})")
        check("CI declares at least one runner", bool(runners))
        check("CI declares at least one python version", bool(pythons))
        for os_name in verified["os"]:
            check(
                f"CI actually runs on claimed OS '{os_name}'",
                any(os_name.split("-")[0] in r for r in runners),
                f"CI runners are {sorted(runners)} — the doc claims more than CI covers",
            )
        for py in verified["python"]:
            check(
                f"CI actually runs claimed Python '{py}'",
                py in pythons,
                f"CI pythons are {sorted(pythons)} — the doc claims more than CI covers",
            )

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} -> {FAILURES}")
        return 1
    if SKIPS:
        # A skip is reported loudly but does not fail: the skill is legitimately installable
        # standalone. In the source repo the check runs, which is where it matters.
        print(f"passed with {len(SKIPS)} skip(s) — see SKIP lines above")
        return 0
    print("support matrix matches CI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
