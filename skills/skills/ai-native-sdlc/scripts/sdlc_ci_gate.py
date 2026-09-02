#!/usr/bin/env python3
"""sdlc_ci_gate.py — CI backstop for the AI-Native SDLC artifact chain.

Where the PreToolUse hook guards ONE session at write time, this guards the MERGE:
it does not care who produced the change, in which session, or whether a hook was
installed. It reads the repo as checked out and fails the build when the chain is
incomplete.

Deliberately the opposite failure posture from the hook:
  - the hook FAILS OPEN  (a buggy gate must not stop you editing files)
  - this   FAILS CLOSED  (anything it cannot verify is a red check)

Usage:
    sdlc_ci_gate.py [--repo .] [--changed-files-from <file>] [--require-active]

Exit 0 = chain valid, exit 1 = violation (prints a report).

What it checks
  1. Every intent/<slug>/ has intent.md, and any spec.md/plan.md present carry a
     recognised **Status:** line.
  2. Status ladder is not skipped: a signed-off spec requires an accepted intent;
     an accepted plan requires a signed-off spec.
  3. No artifact is left as the unfilled template placeholder
     ("draft | accepted | rejected").
  4. If a changed-files list is supplied, any change touching a source file must be
     covered by an intent whose plan.md is accepted.
  5. With --require-active, .sdlc/active must exist and name a real intent dir.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ACCEPTED = "accepted"
SIGNED_OFF = "signed-off"

SOURCE_SUFFIXES = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
    ".html", ".css", ".sh", ".sql",
)
# Paths that are process/meta, not the product; they never need plan coverage.
META_DIRS = (".sdlc", "intent", "evals", ".github", "docs")
META_FILES = ("REVIEW.md", "bands.yaml", "CLAUDE.md", "README.md")


def status_of(path: pathlib.Path) -> str:
    if not path.is_file():
        return "<missing>"
    m = re.search(
        r"(?im)^\s*[-*]?\s*\*\*Status:\*\*\s*(.+?)\s*$",
        path.read_text(encoding="utf-8", errors="replace"),
    )
    if not m:
        return "<no-status>"
    raw = m.group(1).strip()
    if "|" in raw:
        return "<unset-template>"
    return raw.casefold()


def satisfies(status: str, needed: str) -> bool:
    """Whole-token, case-insensitive status match.

    DUPLICATED DELIBERATELY from scripts/sdlc_gate.py. This file is vendored into
    each repo as .sdlc/scripts/sdlc_ci_gate.py and must run standalone in CI with
    no imports, so it cannot share the helper. The two copies MUST agree, and
    test_ci_gate.py asserts they do on a shared table of statuses — a divergence
    means a repo passes one gate and fails the other.

    Whole tokens, not substrings: "not-accepted" must not satisfy "accepted".
    Split on whitespace only, so the hyphenated "signed-off" stays one token.
    """
    return needed.casefold() in status.casefold().split()


def is_meta(rel: str) -> bool:
    p = rel.replace("\\", "/")
    if pathlib.PurePosixPath(p).name in META_FILES:
        return True
    return any(seg in META_DIRS for seg in p.split("/") if seg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--changed-files-from", default="")
    ap.add_argument("--require-active", action="store_true")
    args = ap.parse_args()

    root = pathlib.Path(args.repo).resolve()
    problems: list[str] = []
    notes: list[str] = []

    intent_root = root / "intent"
    slugs = (
        sorted(p.name for p in intent_root.iterdir() if p.is_dir())
        if intent_root.is_dir()
        else []
    )

    if not slugs:
        notes.append("no intent/<slug>/ directories found — SDLC chain not in use here")

    plan_accepted: set[str] = set()

    for slug in slugs:
        d = intent_root / slug
        s_intent = status_of(d / "intent.md")
        s_spec = status_of(d / "spec.md")
        s_plan = status_of(d / "plan.md")

        if s_intent == "<missing>":
            problems.append(f"intent/{slug}/: intent.md is missing (Stage 1 artifact)")
        for name, st in (("intent.md", s_intent), ("spec.md", s_spec), ("plan.md", s_plan)):
            if st == "<unset-template>":
                problems.append(
                    f"intent/{slug}/{name}: Status is still the unfilled template "
                    f"placeholder — fill it in with a single value"
                )
            elif st == "<no-status>":
                problems.append(f"intent/{slug}/{name}: no '**Status:**' line found")

        # Ladder: cannot sign off a spec without an accepted intent.
        if satisfies(s_spec, SIGNED_OFF) and not satisfies(s_intent, ACCEPTED):
            problems.append(
                f"intent/{slug}/: spec.md is signed-off but intent.md is '{s_intent}' "
                f"(need '{ACCEPTED}') — a stage was skipped"
            )
        # Ladder: cannot accept a plan without a signed-off spec.
        if satisfies(s_plan, ACCEPTED) and not satisfies(s_spec, SIGNED_OFF):
            problems.append(
                f"intent/{slug}/: plan.md is accepted but spec.md is '{s_spec}' "
                f"(need '{SIGNED_OFF}') — a stage was skipped"
            )

        if (
            satisfies(s_plan, ACCEPTED)
            and satisfies(s_spec, SIGNED_OFF)
            and satisfies(s_intent, ACCEPTED)
        ):
            plan_accepted.add(slug)

    if args.require_active:
        active = root / ".sdlc" / "active"
        if not active.is_file():
            problems.append(".sdlc/active is missing but --require-active was set")
        else:
            slug = active.read_text(encoding="utf-8").strip().splitlines()
            slug = slug[0].strip() if slug else ""
            if not slug:
                problems.append(".sdlc/active is empty")
            elif not (intent_root / slug).is_dir():
                problems.append(f".sdlc/active names '{slug}' but intent/{slug}/ does not exist")

    # Source-file coverage.
    if args.changed_files_from:
        listing = pathlib.Path(args.changed_files_from)
        if not listing.is_file():
            problems.append(f"changed-files list not found: {listing}")
        else:
            changed = [
                ln.strip()
                for ln in listing.read_text(encoding="utf-8").splitlines()
                if ln.strip()
            ]
            source_changed = [
                c for c in changed if c.endswith(SOURCE_SUFFIXES) and not is_meta(c)
            ]
            if source_changed and not plan_accepted:
                problems.append(
                    "source files changed but NO intent has a fully accepted chain "
                    "(intent accepted + spec signed-off + plan accepted):\n    "
                    + "\n    ".join(source_changed[:20])
                )
            elif source_changed:
                notes.append(
                    f"{len(source_changed)} source file(s) changed; "
                    f"accepted chain(s): {', '.join(sorted(plan_accepted))}"
                )
            else:
                notes.append("no product source files changed")

    for n in notes:
        print(f"note: {n}")

    if problems:
        print()
        print(f"SDLC CI GATE FAILED ({len(problems)} problem(s)):")
        for p in problems:
            print(f"  - {p}")
        print()
        print("The artifact chain must be intent.md (accepted) -> spec.md (signed-off)")
        print("-> plan.md (accepted) before product source code is merged.")
        return 1

    print("SDLC CI GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
