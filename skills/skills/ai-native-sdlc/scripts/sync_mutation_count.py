#!/usr/bin/env python3
"""sync_mutation_count.py — write the harness's real mutation count into the documents.

WHY THIS EXISTS: the count lived as a hand-typed literal in three places -- SKILL.md,
references/limitations.md, and (via its anchor) the stale-count entry in mutation_proof.py.
Every change to the mutation set had to update all of them or the build went red for a reason
unrelated to the change being made. That happened four times in one working session.

This command removes the hand-edit from the two documents. It does NOT relax the freshness
check: test_enterprise_readiness.py still fails when a document disagrees with the harness, and
that is what catches a human who forgets to run this.

    python3 sync_mutation_count.py            # rewrite the documents
    python3 sync_mutation_count.py --check    # exit 1 if stale; write nothing

Design notes worth keeping:

  * The count is read by PARSING the harness with ast, not by importing it. Importing would
    execute module-level code and couple this tool to the harness's runtime rather than its data.
  * A target sentence that does not match is a HARD ERROR. Silently skipping a target is exactly
    how a stale "27 mutations" claim survived unnoticed for months, so the failure mode has to be
    loud.
  * No MUTATIONS list is an error too, never a count of zero. Writing "0 mutations, all killed"
    would be a false evidence claim produced by a tool meant to keep evidence honest.

Standard library only.
"""

from __future__ import annotations

import argparse
import ast
import pathlib
import re
import sys


class SyncError(RuntimeError):
    """A condition the caller must fix; never worked around silently."""


# Each target: the file, and a regex whose single group is the number to replace. The wording
# around the group may change freely; only the shape has to hold.
TARGETS: tuple[tuple[str, str], ...] = (
    ("SKILL.md", r"(?P<n>\d+) mutations, all"),
    ("references/limitations.md", r"\((?P<n>\d+) mutations, (?P=n) killed\)"),
)


def mutation_count(harness: pathlib.Path) -> int:
    """Count MUTATIONS entries by parsing the harness. Never import it, never trust a literal."""
    try:
        src = harness.read_text(encoding="utf-8")
    except OSError as exc:
        raise SyncError(f"cannot read the harness at {harness}: {exc}") from exc
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        raise SyncError(f"{harness} does not parse: {exc}") from exc

    for node in ast.walk(tree):
        # The real harness uses the annotated form; accept the plain form so this does not
        # depend on that staying put.
        if isinstance(node, ast.Assign):
            targets, value = list(node.targets), node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "MUTATIONS":
                if isinstance(value, (ast.List, ast.Tuple)):
                    return len(value.elts)
                raise SyncError(f"{harness}: MUTATIONS is not a list or tuple literal")

    raise SyncError(
        f"{harness}: no MUTATIONS list found. Refusing to treat that as a count of zero — "
        "a tool that keeps evidence honest must not invent evidence."
    )


def apply_to(path: pathlib.Path, pattern: str, count: int, *, write: bool) -> bool:
    """Return True when the file is already current. Raise when the target sentence is absent."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SyncError(f"cannot read {path.name} at {path}: {exc}") from exc

    rx = re.compile(pattern)
    matches = list(rx.finditer(text))
    if not matches:
        raise SyncError(
            f"{path.name}: no sentence matching /{pattern}/ — refusing to skip it silently. "
            "Either the wording changed and this tool needs updating, or the claim was removed."
        )

    stale = [m for m in matches if int(m.group("n")) != count]
    if not stale:
        return True
    if not write:
        found = ", ".join(sorted({m.group("n") for m in stale}))
        raise SyncError(
            f"{path.name}: states {found} mutations but the harness has {count}. "
            "Run sync_mutation_count.py to update it."
        )

    def sub(m: re.Match[str]) -> str:
        return m.group(0).replace(m.group("n"), str(count))

    path.write_text(rx.sub(sub, text), encoding="utf-8")
    return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--root",
        default=str(pathlib.Path(__file__).resolve().parent.parent),
        help="skill root containing SKILL.md, references/ and scripts/ (default: this skill)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="report staleness and change nothing; exit 1 when a document is out of date",
    )
    args = ap.parse_args(argv)

    root = pathlib.Path(args.root).resolve()
    harness = root / "scripts" / "mutation_proof.py"

    try:
        count = mutation_count(harness)
        # Resolve every target before writing any, so a bad target cannot leave the documents
        # half-updated and disagreeing with each other.
        paths = []
        for rel, pattern in TARGETS:
            p = root / rel
            if not p.is_file():
                raise SyncError(f"{rel}: not found under {root}")
            paths.append((p, pattern))

        already = []
        for p, pattern in paths:
            already.append(apply_to(p, pattern, count, write=not args.check))
    except SyncError as exc:
        print(f"sync_mutation_count: {exc}", file=sys.stderr)
        return 1

    if args.check:
        print(f"sync_mutation_count: {count} mutations; documents agree")
        return 0

    changed = [rel for (rel, _), ok in zip(TARGETS, already) if not ok]
    if changed:
        print(f"sync_mutation_count: wrote {count} into " + ", ".join(changed))
    else:
        print(f"sync_mutation_count: {count} mutations; nothing to change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
