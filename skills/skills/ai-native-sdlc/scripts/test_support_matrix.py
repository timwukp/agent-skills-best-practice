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
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
COMPAT = SKILL / "COMPATIBILITY.md"

FAILURES: list[str] = []
SKIPS: list[str] = []


def _git(root: pathlib.Path, *args: str) -> tuple[bool, str]:
    """Run a read-only git command in `root`. Returns (ok, stdout).

    Deliberately local-only: a test that reaches the network is flaky by construction and
    would fail in an offline install. CI supplies the objects instead, which is why the
    suite job checks out with fetch-depth: 0 — without it the runner has no tags and this
    check would skip in exactly the place releases are made.
    """
    try:
        p = subprocess.run(
            ["git", *args], cwd=str(root), capture_output=True, text=True, timeout=30
        )
    except (OSError, subprocess.SubprocessError):
        return False, ""
    return p.returncode == 0, p.stdout


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

    # Platform caveats must be spelled out in prose, not merely encoded. "windows-latest is
    # verified" is true of the CI gate and false of the local hook, and a reader who only
    # sees the OS row would draw the wrong conclusion.
    posix_only = block.get("posix_only", [])
    check(
        "posix_only caveats are declared",
        bool(posix_only),
        "the shipped hook command is a POSIX sh string; that limit must be recorded",
    )
    for item in posix_only:
        # Match on a distinctive fragment rather than the whole sentence, so prose can be
        # reworded without breaking the test, while still requiring the subject be named.
        key = "templates/kiro-hooks" if "kiro-hooks" in item else item
        check(f"prose explains the POSIX-only limit for '{key}'", key in text)
    if posix_only:
        check(
            "prose says Windows lacks the write-time hook",
            "POSIX-only" in text and "Windows" in text,
        )

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

    # --- Pin guidance must reference a tag that actually exists ---------------------
    # COMPATIBILITY.md recommends pinning the reusable workflow. It recommended @v1, a ref
    # that does not exist among the sdlc-gate-vN tags, and its table claimed a bare `vN`
    # moving tag. A consumer following the recommendation cannot even resolve the workflow.
    # Assert the real convention (sdlc-gate-vN) in the pin examples that name the reusable
    # workflow, and that no bare-vN moving tag is claimed.
    pin_lines = [
        ln for ln in text.splitlines()
        if "sdlc-gate-reusable.yml@" in ln
    ]
    check("COMPATIBILITY.md has reusable-workflow pin examples", bool(pin_lines))
    for ln in pin_lines:
        ref = ln.split("sdlc-gate-reusable.yml@", 1)[1].strip()
        # A full-SHA example and a placeholder <full-sha> are both fine; a tag example must
        # use the real prefix rather than a bare vN that has no matching ref.
        bare_vn = re.fullmatch(r"v\d+", ref) is not None
        check(
            f"pin example uses a real ref, not a nonexistent bare vN ({ref})",
            not bare_vn,
            f"-> {ln.strip()}",
        )
    check(
        "versioning table does not claim a bare `vN` moving tag",
        "`vN` moving tag" not in text,
    )

    # --- Pin guidance must reference a ref that WORKS, not merely one that resolves ---
    # The check above asserts the pin NAMES a real ref. That is not the property a
    # consumer needs, and the gap was not theoretical: every released tag
    # (sdlc-gate-v1, v2, v2.0.1, v2.0.2) ships a reusable workflow that passes NO
    # --base-sha, while gate v2 makes `Accepted-for` mandatory and fails closed when it
    # cannot verify the binding. So the documented pin refused every compliant
    # consumer's pull request while three separate assertions stayed green:
    #
    #   * U9  (test_unbound_approval) asserts the shipped TEMPLATE passes --base-sha
    #   * U10 (test_unbound_approval) asserts the WORKING TREE's reusable workflow does
    #   * the check above asserts the recommended pin NAMES an existing tag
    #
    # All three inspect the working tree or the ref's NAME. None inspects the CONTENT at
    # the ref we tell consumers to use, which is the only thing that determines whether
    # following our documentation produces a working gate.
    #
    # This assertion is what makes the recommendation self-checking: a pin cannot be
    # recommended unless the workflow at that ref actually verifies the binding. It also
    # polices the eventual switch from a SHA pin to a release tag — a tag whose content
    # omits --base-sha is refused, so that move cannot be made incorrectly.
    #
    # It targets the step that RUNS the gate, so a comment mentioning --base-sha cannot
    # satisfy it. Placeholder examples (<full-sha>) instruct rather than recommend and are
    # skipped. An unresolvable ref is a SKIP, not a failure: the skill is installed
    # standalone into repositories that have never heard of sdlc-gate-vN, and a suite that
    # fails there would be worse than the defect it guards.
    git_root = None
    for parent in [SKILL, *SKILL.parents]:
        if (parent / ".git").exists():
            git_root = parent
            break
    # Under mutation this suite runs in a bare sandbox with no .git, so the walk above finds
    # nothing and this check would SKIP — letting the mutation survive and reporting the guard
    # as absent. The harness therefore passes the real repository root. Only GIT reads use it:
    # `text` still comes from the sandbox, so the suite learns WHICH ref is recommended from
    # the mutated document and reads only that ref's committed content, which no mutation can
    # alter. Absent, the skip below still applies.
    if git_root is None:
        hinted = os.environ.get("SDLC_GIT_REPO", "")
        if hinted and (pathlib.Path(hinted) / ".git").exists():
            git_root = pathlib.Path(hinted)

    if git_root is None:
        print("  skip pin-content check — no git repository above the skill")
    else:
        # Requirement 3': an unresolvable ref is a FAILURE when this repository demonstrably
        # should be able to resolve it, and a SKIP otherwise. An unconditional skip let a
        # mistyped or deleted tag pass BOTH checks -- the name check only rejects a bare vN --
        # so a recommendation naming a ref that cannot exist shipped green, which is the same
        # class of defect this assertion exists to close, one level out.
        #
        # The three cases are NOT interchangeable. Failing on a missing SHA would break every
        # legitimately shallow or partial clone, because those lack old objects by design. Only
        # a TAG absent from a TAGGED repository is safely diagnosable as an error.
        have_tags, tag_out = _git(git_root, "tag", "-l", "sdlc-gate-*")
        gate_tags = [t for t in tag_out.split() if t] if have_tags else []
        _, shallow_out = _git(git_root, "rev-parse", "--is-shallow-repository")
        shallow = shallow_out.strip() == "true"
        depth_note = " (shallow clone)" if shallow else ""

        for ln in pin_lines:
            ref = ln.split("sdlc-gate-reusable.yml@", 1)[1].strip()
            if "<" in ref or ">" in ref:
                print(f"  skip pin-content check — placeholder, not a recommendation ({ref})")
                continue
            resolved, _ = _git(git_root, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}")
            if not resolved:
                looks_like_gate_tag = ref.startswith("sdlc-gate-v")
                if looks_like_gate_tag and gate_tags:
                    check(
                        f"recommended tag {ref} exists",
                        False,
                        f"— this repository has gate tags {sorted(gate_tags)} but not {ref}, so "
                        f"the recommendation names a tag that was mistyped or deleted. A "
                        f"consumer copying it cannot resolve the workflow at all.",
                    )
                elif looks_like_gate_tag:
                    print(
                        f"  skip pin-content check — no sdlc-gate-* tags in this repository"
                        f"{depth_note}, cannot judge {ref}"
                    )
                else:
                    print(
                        f"  skip pin-content check — {ref} is not an object in this clone"
                        f"{depth_note}; a shallow or partial clone legitimately lacks it"
                    )
                continue
            got, wf = _git(git_root, "show", f"{ref}:.github/workflows/sdlc-gate-reusable.yml")
            if not got:
                check(
                    f"recommended ref {ref} provides the reusable workflow",
                    False,
                    "— the pin resolves but the workflow is absent at that ref, so a "
                    "consumer following this recommendation cannot run the gate at all.",
                )
                continue
            m = re.search(r"python3[^\n]*sdlc_ci_gate\.py", wf)
            idx = m.start() if m else -1
            window = wf[max(0, idx - 800): idx + 400] if idx >= 0 else ""
            check(
                f"recommended pin {ref} passes --base-sha to the gate",
                idx >= 0 and "--base-sha" in window,
                f"— the workflow at {ref} runs the gate without --base-sha, so gate v2 "
                f"fails closed on every pull request whose plan records `Accepted-for`. "
                f"The fix exists on main; this ref predates it. Recommend a ref whose "
                f"content verifies the binding.",
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
