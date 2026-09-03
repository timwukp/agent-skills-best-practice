#!/usr/bin/env python3
"""test_fork_safety.py — fork-based pull requests, the last untested repo shape.

WHAT CANNOT BE TESTED HERE, STATED UP FRONT: real fork-PR token semantics need a pull
request opened from a SECOND GitHub account. There is one account available, and a user
cannot fork their own repository, so the live behaviour is genuinely unverifiable in this
environment. Claiming otherwise would be the weak-eval failure mode.

What IS verifiable is the fork-safety CONTRACT, and every clause below is a real hazard:

  1. `pull_request_target` must never be used. It runs with a WRITE-scoped token in the
     base repo's context while processing an untrusted fork's diff -- the single change
     that would turn every prompt-injection finding in the threat model into repository
     compromise.
  2. The gate job must not depend on any secret. Fork PRs receive NO secrets, so a gate
     that needs one silently degrades or fails on exactly the contributions that most need
     checking.
  3. The advisory review job must not be able to FAIL the build. GitHub downgrades the
     workflow token to READ-ONLY on a fork PR regardless of the `permissions:` block, so an
     unguarded `createComment` throws 403 and fails the step -- an "advisory" job blocking a
     PR. Today that is unreachable only because forks also lack the API key, which is
     accidental safety, not designed safety.

These are asserted against the shipped template, so the properties cannot be edited away
without the build going red.
"""

from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / "templates" / "github-workflows" / "sdlc-gate.yml"
REUSABLE_HINT = "sdlc-gate-reusable.yml"

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def load() -> str:
    if not TEMPLATE.is_file():
        print(f"  FAIL template missing at {TEMPLATE}")
        FAILURES.append("template missing")
        return ""
    return TEMPLATE.read_text(encoding="utf-8")


def test_no_pull_request_target(text: str) -> None:
    print("1. pull_request_target must never be used")
    # Only count it as a trigger if it appears as a YAML key, not inside a comment warning
    # against it -- the template deliberately DOCUMENTS the hazard.
    trigger_lines = [
        ln for ln in text.splitlines()
        if re.match(r"^\s{0,4}pull_request_target\s*:", ln)
    ]
    check("no pull_request_target trigger", not trigger_lines, f"found: {trigger_lines}")
    # And the hazard must be documented, so a future editor knows why it is absent.
    check(
        "the template warns against pull_request_target",
        "pull_request_target" in text,
        "absence alone is fragile — someone will add it unless told why not to",
    )


def test_gate_needs_no_secret(text: str) -> None:
    print("2. the gate job must not depend on a secret")
    # Split at the review job; everything before it is the gate.
    idx = text.find("sdlc-review")
    gate_part = text[:idx] if idx > 0 else text
    secrets_in_gate = re.findall(r"secrets\.([A-Z_][A-Z0-9_]*)", gate_part)
    check(
        "gate section references no secrets",
        not secrets_in_gate,
        f"a fork PR gets no secrets, so these would be empty: {sorted(set(secrets_in_gate))}",
    )


def test_advisory_job_cannot_fail_the_build(text: str) -> None:
    print("3. the advisory review job must not be able to fail the build")

    # The kiro-cli invocation must swallow its own failure.
    check(
        "the review command tolerates its own failure",
        "|| true" in text,
        "a review problem must not fail the build",
    )

    # The comment POST must be guarded. On a fork PR the token is READ-ONLY, so an
    # unguarded createComment throws and fails the step.
    #
    # NOTE ON THIS ASSERTION: a first draft searched for "try {" and "catch" in a window
    # AROUND createComment and PASSED FALSELY -- the script already contains
    # `try { fs.readFileSync(...) } catch (e) {}` guarding the FILE READ, which says nothing
    # about the network call. The check must therefore prove the catch comes AFTER the
    # createComment call, i.e. actually encloses it.
    m = re.search(r"createComment\(", text)
    check("a comment step exists", bool(m))
    if m:
        after = text[m.end(): m.end() + 700]
        has_catch_after = re.search(r"\}\s*catch\b", after) is not None
        check(
            "createComment is enclosed by a try/catch (catch appears AFTER the call)",
            has_catch_after,
            "on a fork PR the token is read-only; an unguarded createComment 403s and "
            "turns the advisory job into a blocking one. A try/catch that only guards the "
            "file read does not count.",
        )
        check(
            "the catch explains it is non-fatal rather than swallowing silently",
            has_catch_after and re.search(r"catch[\s\S]{0,300}?(core\.warning|console\.log|advisory|read-only)", after) is not None,
            "a bare `catch (e) {}` hides a real permissions problem from the maintainer",
        )

    # continue-on-error on the job is the belt to that braces.
    check(
        "the review job is marked continue-on-error",
        re.search(r"continue-on-error:\s*true", text) is not None,
        "an advisory job should not be able to fail a build even if a step misbehaves",
    )


def test_fork_behaviour_documented() -> None:
    print("4. the fork limitation must be documented, not implied")
    compat = SKILL / "COMPATIBILITY.md"
    text = compat.read_text(encoding="utf-8") if compat.is_file() else ""
    check("COMPATIBILITY.md mentions fork PRs", "fork" in text.lower())

    # Scope the claim to the FORK SECTION. A first draft searched the whole document and
    # survived a mutation that deleted the claim from the fork sentence, because "read-only"
    # also appears in unrelated prose elsewhere. Document-wide substring checks are not
    # assertions about the thing you meant.
    m = re.search(r"^###\s+Fork-based pull requests.*$", text, re.MULTILINE)
    check("a dedicated fork section exists", bool(m))
    if m:
        rest = text[m.end():]
        nxt = re.search(r"^###\s", rest, re.MULTILINE)
        section = rest[: nxt.start()] if nxt else rest
        check(
            "the fork section states forks get NO SECRETS",
            "no secrets" in section.lower(),
            "an adopter must know the review pass cannot run on fork contributions",
        )
        check(
            "the fork section states the token is READ-ONLY",
            "read-only" in section.lower(),
            "the read-only token is why the comment POST must not be able to fail the job",
        )
        check(
            "the fork section is honest that live semantics are unverified",
            "unverified" in section.lower() or "unproven" in section.lower(),
            "contract-tested is not runtime-tested; say so",
        )


def main() -> int:
    text = load()
    if not text:
        print("\nFAILED: template unreadable")
        return 1
    test_no_pull_request_target(text)
    test_gate_needs_no_secret(text)
    test_advisory_job_cannot_fail_the_build(text)
    test_fork_behaviour_documented()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} -> {FAILURES}")
        return 1
    print("all fork-safety tests passed")
    print("NOTE: live fork-PR token semantics remain UNVERIFIED — that needs a second "
          "GitHub account. Contract only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
