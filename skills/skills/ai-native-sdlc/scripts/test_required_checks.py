#!/usr/bin/env python3
"""test_required_checks.py — a required status check must be able to REPORT.

A required check whose workflow cannot be triggered for a given pull request does
not fail that PR; it leaves it BLOCKED forever, waiting for a status that can never
arrive. Waiting does not help and there is no run to re-run. This is an availability
failure for the whole team, produced by the mechanism that is supposed to protect it.

Observed TWICE in this repository, from two different filters:

1. `paths:` on `pull_request` — a doc-only PR touched nothing under the filter, so
   `gate tests green` never reported. Fixed by removing the filter; the comment in
   sdlc-gate-tests.yml records why it must not come back.

2. `branches:` on `pull_request` — the STACKED-PR variant, and the one this suite was
   written for. PR #53 was opened with base `fix-unbound-approval`. Merging #52
   auto-retargeted it to `main`, so main's protection began requiring `validate` —
   but `validate` had never run, because when the event fired the base did not match
   `branches: [main]`. Retargeting does NOT re-trigger `pull_request` workflows, so no
   run existed to re-run. The merge box read "Expected — Waiting for status to be
   reported" indefinitely. Unblocked only by closing and reopening the PR.

Both filters are individually reasonable and both are fatal on a REQUIRED check. The
tension is inherent: required checks assume the check always reports, conditional
triggers assume it sometimes should not. For a required check the conditional loses.

This also covers the workflow the skill SHIPS to consumers, which matters more than
this repo's own CI: the skill's docs tell adopters to make `sdlc-gate` a required
check, so shipping it with a trigger filter hands them the same deadlock in their own
repository, where they have none of this context to diagnose it.

No PyYAML: the CI matrix spans five Python versions on three operating systems with
no guarantee the module is present, and the neighbouring suites parse these files
textually for the same reason. Adding a dependency to a test that guards CI would be
its own availability risk.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent

FAILURES: list[str] = []
SKIPS: list[str] = []

# The contexts branch protection actually requires on main, read off the live API
# (repos/{o}/{r}/branches/main/protection -> required_status_checks.contexts) rather
# than guessed. A required context is spelled with its DISPLAY name: the job id
# `gate-tests-green` surfaces as the check `gate tests green`, and requiring the wrong
# spelling is itself a permanent block.
REQUIRED_CONTEXTS = ("gate tests green", "validate")

# Filters that can stop a pull_request event from ever reaching the workflow. Both
# have caused a real deadlock here.
FATAL_ON_REQUIRED = ("branches", "paths", "branches-ignore", "paths-ignore")


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def find_repo_root() -> pathlib.Path | None:
    """Walk up for .github/workflows. Absent when the skill is installed standalone."""
    for parent in [SKILL, *SKILL.parents]:
        if (parent / ".github" / "workflows").is_dir():
            return parent
    return None


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def pull_request_filters(text: str) -> list[str] | None:
    """Filter keys under the `pull_request:` trigger. None when there is no such trigger.

    Deliberately textual and shallow -- it reads the `on:` mapping, finds the
    `pull_request:` key inside it, and returns the keys of that block. It does not try
    to be a YAML parser; it only has to answer "is this trigger conditional".
    """
    lines = text.splitlines()
    on_idx = None
    for i, ln in enumerate(lines):
        # `on:` at column 0, allowing the quoted form some linters prefer.
        if re.match(r"""^(on|["']on["']):\s*$""", ln):
            on_idx = i
            break
    if on_idx is None:
        return None

    # The on-block is everything more indented than `on:` until the next dedent.
    pr_idx = None
    pr_indent = None
    for i in range(on_idx + 1, len(lines)):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if indent_of(ln) == 0:
            break
        if re.match(r"^\s+pull_request:\s*$", ln):
            pr_idx, pr_indent = i, indent_of(ln)
            break
    if pr_idx is None:
        return None

    keys: list[str] = []
    for i in range(pr_idx + 1, len(lines)):
        ln = lines[i]
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        if indent_of(ln) <= pr_indent:
            break
        m = re.match(r"^\s+([A-Za-z_-]+):", ln)
        if m:
            keys.append(m.group(1))
    return keys


root = find_repo_root()

# ---- 1. the workflow the skill SHIPS ---------------------------------------
# Checked first and unconditionally: it is present wherever the skill is, and a
# deadlock shipped to a consumer is worse than one in our own CI.
tpl = SKILL / "templates" / "github-workflows" / "sdlc-gate.yml"
if not tpl.is_file():
    FAILURES.append("shipped template sdlc-gate.yml is missing")
else:
    keys = pull_request_filters(tpl.read_text(encoding="utf-8"))
    check("shipped template has a pull_request trigger", keys is not None)
    if keys is not None:
        bad = [k for k in keys if k in FATAL_ON_REQUIRED]
        check(
            "shipped template's pull_request trigger is unconditional",
            not bad,
            f"— found {bad}. The skill tells adopters to make this check REQUIRED, so a "
            f"filter here deadlocks any of their PRs the filter excludes (a stacked PR, "
            f"a PR onto a release branch, a doc-only PR).",
        )

# ---- 2. this repo's own required checks ------------------------------------
if root is None:
    SKIPS.append("no .github/workflows above the skill — repo CI not checked")
else:
    wfs = sorted((root / ".github" / "workflows").glob("*.yml"))
    check("repo has workflows to inspect", bool(wfs))

    for ctx in REQUIRED_CONTEXTS:
        # Find the workflow producing this context. A context is produced either by a
        # job `name:` or, absent that, by its job id.
        producers = []
        for wf in wfs:
            text = wf.read_text(encoding="utf-8")
            if re.search(rf"^\s*name:\s*['\"]?{re.escape(ctx)}['\"]?\s*$", text, re.M):
                producers.append(wf)
            elif re.search(rf"^  {re.escape(ctx.replace(' ', '-'))}:\s*$", text, re.M):
                producers.append(wf)

        # A required context nothing produces blocks every PR forever -- the same
        # failure as a filtered trigger, reached by renaming or deleting a job.
        check(
            f"required context {ctx!r} is produced by some workflow",
            bool(producers),
            "— branch protection requires a check no workflow reports; every PR is "
            "blocked permanently until the name is fixed or the requirement dropped.",
        )

        for wf in producers:
            keys = pull_request_filters(wf.read_text(encoding="utf-8"))
            check(
                f"{wf.name} has a pull_request trigger (required context {ctx!r})",
                keys is not None,
                "— a required check whose workflow never runs on pull requests can "
                "never report.",
            )
            if keys is not None:
                bad = [k for k in keys if k in FATAL_ON_REQUIRED]
                check(
                    f"{wf.name}'s pull_request trigger is unconditional",
                    not bad,
                    f"— found {bad}. Keep such filters on `push:` (a skipped push run "
                    f"blocks nothing, because required checks only apply to PRs), never "
                    f"on `pull_request:`.",
                )

# ---- 3. the reason must stay written down ----------------------------------
# The filter was removed once before and the only thing stopping it returning is the
# comment explaining why. Assert the explanation survives, not merely the absence.
tests_wf = None if root is None else root / ".github" / "workflows" / "sdlc-gate-tests.yml"
if tests_wf is not None and tests_wf.is_file():
    t = tests_wf.read_text(encoding="utf-8")
    check(
        "sdlc-gate-tests.yml still explains why pull_request must stay unfiltered",
        "DO NOT add a paths filter here" in t,
        "— the warning comment is the only thing preventing a well-meaning "
        "reintroduction of a permanent block.",
    )

for s in SKIPS:
    print(f"  skip {s}")
print("required-checks:", "FAIL" if FAILURES else "all pass")
for f in FAILURES:
    print("  -", f)
sys.exit(1 if FAILURES else 0)
