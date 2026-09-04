#!/usr/bin/env python3
"""sdlc_gate.py — enforce AI-native SDLC stage ordering for one change.

A stage may not start until the prior stage's artifact exists AND is accepted.
This is the deterministic layer behind the advisory skill: wire it into a
PreToolUse hook (block edits before plan.md is accepted) or run it in CI.

Usage:
    sdlc_gate.py <intent-dir> <stage>
      stage in: design | build | test | deploy
Exit 0 = gate open, exit 2 = gate closed (blocking), with reason on stderr.
"""
import sys
import pathlib
import re

ACCEPTED = "accepted"
SIGNED_OFF = "signed-off"

# Terminal status. An intent whose change has merged is `shipped`, and a shipped
# intent may not authorise further work: the approval was granted for a diff that
# is already in main, so reusing it silently launders a NEW change through an OLD
# signature. Nothing here needs to special-case it in status_satisfies() -- that
# matcher compares whole tokens, so "shipped" already fails to satisfy "accepted".
# The constant exists so both gates name the same state instead of each spelling a
# string literal, and so the refusal path can tell "not finished yet" apart from
# "already spent" -- two situations with opposite correct fixes.
SHIPPED = "shipped"

REQUIRED = {
    "design": [("intent.md", "accepted")],
    "build":  [("intent.md", "accepted"), ("spec.md", "signed-off")],
    "test":   [("spec.md", "signed-off"), ("plan.md", "accepted")],
    "deploy": [("plan.md", "accepted")],
}


def status_of(path: pathlib.Path) -> str:
    if not path.exists():
        return "<missing>"
    text = path.read_text(encoding="utf-8", errors="replace")
    # [ \t]* not \s* around the value: \s matches newlines, so with an EMPTY value
    # the pattern would consume the line break and capture the NEXT line's text.
    m = re.search(r"(?im)^[ \t]*[-*]?[ \t]*\*\*Status:\*\*[ \t]*(.*?)[ \t]*$", text)
    if not m:
        return "<no-status>"
    raw = m.group(1).strip()
    if not raw:
        return "<empty-status>"
    # A pipe-separated line (e.g. "draft | accepted | rejected") is the unfilled
    # template placeholder, not a real status — a real status is a single token.
    if "|" in raw:
        return "<unset-template>"
    return raw


def status_satisfies(status: str, needed: str) -> bool:
    """True when *status* really is *needed*.

    Compared case-insensitively as WHOLE whitespace-separated tokens, which is
    load-bearing in two ways a substring check got wrong:

    - "Accepted" / "ACCEPTED" mean "accepted"; a case-sensitive check silently
      refused a correctly-accepted artifact forever.
    - "not-accepted", "unaccepted" and "preaccepted" all CONTAIN "accepted" but
      are refusals. A substring check opened the gate on an explicit rejection.

    Splitting on whitespace only (not on every non-word character) is required so
    that the hyphenated value "signed-off" stays one token while "not-accepted"
    also stays one token and therefore does not match "accepted".

    Trailing detail is still honoured: "accepted by the product owner" contains
    "accepted" as its own token and passes.
    """
    return needed.casefold() in status.casefold().split()


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    intent_dir = pathlib.Path(sys.argv[1])
    stage = sys.argv[2].lower()
    if stage not in REQUIRED:
        print(f"unknown stage: {stage}", file=sys.stderr)
        return 2
    problems = []
    terminal = []
    for fname, needed in REQUIRED[stage]:
        st = status_of(intent_dir / fname)
        if not status_satisfies(st, needed):
            problems.append(f"{fname}: status is '{st}', need '{needed}'")
            if status_satisfies(st, SHIPPED):
                terminal.append(fname)
    if problems:
        print(f"GATE CLOSED for '{stage}':", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        if terminal:
            # A spent chain, not an unfinished one. The generic advice below would tell
            # the author to accept an artifact that was ALREADY accepted and used, i.e.
            # to reuse one sign-off for two changes. Must stay in step with the same
            # branch in sdlc_ci_gate.py: if the write-time hook and the merge-time gate
            # disagree, the developer writes happily and CI refuses later.
            print(
                f"This intent is '{SHIPPED}' — its approval was granted for a change "
                f"that has already merged.\nOpen a new intent and point .sdlc/active "
                f"at it. Do NOT reset it to '{ACCEPTED}'.",
                file=sys.stderr,
            )
        else:
            print("Produce/accept the prior artifact before advancing.", file=sys.stderr)
        return 2
    print(f"gate open: '{stage}' may proceed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
