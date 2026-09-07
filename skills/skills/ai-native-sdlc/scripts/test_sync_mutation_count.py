"""test_sync_mutation_count.py — the mutation count must be propagated by a command, not by hand.

WHY THIS EXISTS: the count of mutations in mutation_proof.py was written by hand into three
other places, and every change to the mutation set had to update all three or the build went
red for a reason unrelated to the change being made. That fired repeatedly: 65 -> 70 -> 72 -> 73.

sync_mutation_count.py removes the hand-edit. This suite is what stops it silently rotting:

  * the count is DERIVED from the harness's MUTATIONS list, never typed;
  * a stale document is rewritten to agree with the harness;
  * --check reports staleness WITHOUT writing anything, so CI and a human run the same code;
  * a rewrite is idempotent;
  * a target sentence that does not match is a HARD ERROR, because silently skipping is
    precisely how the stale "27 mutations" claim survived for months.

Every case runs against temporary fixtures. Nothing here may touch the repository's own
documents -- a test run that mutates tracked files is a defect, not a test.

Exit 0 = all pass.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TOOL = HERE / "sync_mutation_count.py"

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def run(*args: str, cwd: pathlib.Path | None = None) -> tuple[int, str]:
    """Invoke the tool as a subprocess. Never imported: the tool is a command."""
    p = subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(cwd) if cwd else None,
    )
    return p.returncode, p.stdout + p.stderr


def harness(n: int) -> str:
    """A minimal stand-in for mutation_proof.py carrying exactly n MUTATIONS entries.

    Annotated assignment on purpose: that is the form the real harness uses, and an earlier
    count-derivation bug came from handling only the plain form.
    """
    entries = "\n".join(
        f'    ("m{i}", "impl.py", "suite.py", "find{i}", "repl{i}"),' for i in range(n)
    )
    return (
        "MUTATIONS: list[tuple[str, str, str, str, str]] = [\n"
        f"{entries}\n"
        "]\n"
    )


SKILL_SENTENCE = (
    "- **Prove a test can fail.** Mutate the implementation and confirm the suite goes red\n"
    "  (`scripts/mutation_proof.py` does this for this skill's own gates — {n} mutations, all\n"
    "  killed). A surviving mutation is an untested behaviour, not a pass.\n"
)

LIMITS_SENTENCE = (
    "found and fixed six substantive bugs in itself, and its test suite is mutation-verified\n"
    "({n} mutations, {n} killed). Judged as a personal/small-team tool, the quality holds up.\n"
)


def fixture(root: pathlib.Path, *, harness_n: int, doc_n: int) -> None:
    """Build a fake skill tree: scripts/mutation_proof.py plus the two documents."""
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "references").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "mutation_proof.py").write_text(harness(harness_n), encoding="utf-8")
    (root / "SKILL.md").write_text(
        "# Skill\n\n" + SKILL_SENTENCE.format(n=doc_n), encoding="utf-8"
    )
    (root / "references" / "limitations.md").write_text(
        "# Limitations\n\n" + LIMITS_SENTENCE.format(n=doc_n), encoding="utf-8"
    )


def read_docs(root: pathlib.Path) -> str:
    return (
        (root / "SKILL.md").read_text(encoding="utf-8")
        + (root / "references" / "limitations.md").read_text(encoding="utf-8")
    )


def main() -> int:
    print("sync_mutation_count")

    # The tool not existing yet is the RED state this suite is written for. Report it as a
    # verdict rather than dying on an exec failure, so "red" is a readable result.
    if not TOOL.is_file():
        print(f"  FAIL sync_mutation_count.py does not exist at {TOOL}")
        print("\nFAILED (1): the command has not been implemented yet")
        return 1

    with tempfile.TemporaryDirectory() as t:
        tmp = pathlib.Path(t)

        # --- 1. --check on an ALREADY CURRENT tree: silent success, no writes ---------
        cur = tmp / "current"
        fixture(cur, harness_n=7, doc_n=7)
        before = read_docs(cur)
        code, out = run("--check", "--root", str(cur))
        check("--check exits 0 when documents agree with the harness", code == 0, out.strip()[:160])
        check("--check writes nothing", read_docs(cur) == before)

        # --- 2. --check on a STALE tree: non-zero, still no writes --------------------
        stale = tmp / "stale"
        fixture(stale, harness_n=9, doc_n=7)
        before = read_docs(stale)
        code, out = run("--check", "--root", str(stale))
        check("--check exits non-zero when a document is stale", code != 0, out.strip()[:160])
        check("--check does not repair the file it complains about", read_docs(stale) == before)
        check("--check names the expected count", "9" in out, out.strip()[:160])

        # --- 3. rewrite makes a stale tree current -----------------------------------
        code, out = run("--root", str(stale))
        check("rewrite exits 0", code == 0, out.strip()[:160])
        docs = read_docs(stale)
        check("rewrite writes the harness count into SKILL.md", "9 mutations, all" in docs)
        check("rewrite writes the harness count into limitations.md", "(9 mutations, 9 killed)" in docs)
        check("rewrite leaves no stale count behind", "7 mutations" not in docs)
        code, _ = run("--check", "--root", str(stale))
        check("--check agrees after a rewrite", code == 0)

        # --- 4. idempotence -----------------------------------------------------------
        once = read_docs(stale)
        run("--root", str(stale))
        check("a second rewrite changes nothing", read_docs(stale) == once)

        # --- 5. the annotated-assignment form is counted correctly --------------------
        big = tmp / "big"
        fixture(big, harness_n=73, doc_n=1)
        run("--root", str(big))
        check("counts an annotated MUTATIONS assignment", "73 mutations, all" in read_docs(big))

        # --- 6. an unmatched target is a HARD ERROR, never a silent skip --------------
        broken = tmp / "broken"
        fixture(broken, harness_n=5, doc_n=5)
        (broken / "SKILL.md").write_text(
            "# Skill\n\nThe sentence the tool looks for is gone.\n", encoding="utf-8"
        )
        code, out = run("--root", str(broken))
        check("rewrite fails when a target sentence is absent", code != 0, out.strip()[:160])
        check("the failure names the file it could not patch", "SKILL.md" in out, out.strip()[:160])
        code, out = run("--check", "--root", str(broken))
        check("--check also fails on an absent target sentence", code != 0, out.strip()[:160])

        # --- 7. a harness with no MUTATIONS list is an error, not a count of zero -----
        nolist = tmp / "nolist"
        fixture(nolist, harness_n=3, doc_n=3)
        (nolist / "scripts" / "mutation_proof.py").write_text(
            "SOMETHING_ELSE = []\n", encoding="utf-8"
        )
        code, out = run("--check", "--root", str(nolist))
        check("a harness without MUTATIONS is an error", code != 0, out.strip()[:160])
        check("zero is never silently accepted as the count", "0 mutations" not in read_docs(nolist))

    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}):")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("the mutation count is propagated by the command, not by hand")
    return 0


if __name__ == "__main__":
    sys.exit(main())
