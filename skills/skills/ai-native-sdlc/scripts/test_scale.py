#!/usr/bin/env python3
"""test_scale.py — the repo shapes COMPATIBILITY.md lists as untested.

These are the `documented_untested` repo_shapes: monorepo, multi-intent-pr, concurrent-pr,
polyglot. "Untested" was honest but it is not a resting place -- an unmodelled shape is where
a governance tool silently does the wrong thing.

Each test states the DESIRED behaviour, which is not always "make it work". For a shared
mutable pointer under concurrency the correct outcome is a clear refusal plus a documented
mitigation, not a clever fix that pretends the race is gone.

Exit 0 = all pass.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
GATE = HERE / "sdlc_ci_gate.py"
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
    # Bytes, so line endings are identical on every platform.
    p.write_bytes(text.encode("utf-8"))


def make_intent(root: pathlib.Path, slug: str, files: list[str],
                intent="accepted", spec="signed-off", plan="accepted") -> None:
    """A complete artifact chain for one intent, whose plan names `files`."""
    d = root / "intent" / slug
    hdr = "- **Author:** A. Author\n- **Accepted-by:** B. Approver\n"
    write(d / "intent.md", f"# intent {slug}\n\n{hdr}- **Status:** {intent}\n")
    write(d / "spec.md", f"# spec {slug}\n\n{hdr}- **Status:** {spec}\n")
    listing = "".join(f"- `{f}`\n" for f in files)
    write(d / "plan.md", f"# plan {slug}\n\n{hdr}- **Accepted-for:** {BASE}\n"
          f"- **Status:** {plan}\n\n## Files\n{listing}")


def run_gate(root: pathlib.Path, changed: list[str], extra: list[str] | None = None):
    listing = root / "_changed.txt"
    write(listing, "".join(f"{c}\n" for c in changed))
    cmd = [sys.executable, str(GATE), "--repo", str(root),
           "--base-sha", BASE, "--changed-files-from", str(listing)]
    if extra:
        cmd += extra
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


# ---------------------------------------------------------------- monorepo
def test_monorepo() -> None:
    print("monorepo / multi-intent")

    # Two packages, two intents, each plan naming only its own package's file.
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        write(root / "packages" / "alpha" / "app.py", "x = 1\n")
        write(root / "packages" / "beta" / "app.py", "y = 2\n")
        make_intent(root, "alpha-feat", ["packages/alpha/app.py"])
        make_intent(root, "beta-feat", ["packages/beta/app.py"])
        write(root / ".sdlc" / "version", "1\n")
        write(root / ".sdlc" / "active", "alpha-feat\n")

        # Single-intent PR inside a monorepo must PASS: this is the common case and
        # must not be collateral damage of any multi-intent handling.
        rc, out = run_gate(root, ["packages/alpha/app.py"])
        check("single-intent change in a monorepo passes", rc == 0, out.strip()[-200:])

        # A PR spanning BOTH packages must be refused, and the message must say WHY in
        # monorepo terms. "not named in plan" alone sends the reader to edit the wrong plan.
        rc2, out2 = run_gate(root, ["packages/alpha/app.py", "packages/beta/app.py"])
        check("multi-intent PR is refused", rc2 != 0, out2.strip()[-200:])
        check(
            "refusal names the other intent that owns the file",
            "beta-feat" in out2,
            "the diagnostic should point at the intent that DOES cover the file, "
            f"got: {out2.strip()[-300:]}",
        )

    # A multi-line .sdlc/active must not be silently truncated to its first line.
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        write(root / "packages" / "alpha" / "app.py", "x = 1\n")
        make_intent(root, "alpha-feat", ["packages/alpha/app.py"])
        make_intent(root, "beta-feat", ["packages/beta/app.py"])
        write(root / ".sdlc" / "version", "1\n")
        write(root / ".sdlc" / "active", "alpha-feat\nbeta-feat\n")

        rc, out = run_gate(root, ["packages/alpha/app.py"])
        check(
            "multi-line .sdlc/active is reported, not silently ignored",
            "beta-feat" in out or "one intent" in out.lower() or "single" in out.lower(),
            f"only the first line was used with no diagnostic: {out.strip()[-300:]}",
        )


# ------------------------------------------------------------- concurrency
def test_concurrent() -> None:
    print("concurrent PRs on one .sdlc/active")

    # Each PR is validated against its OWN merge commit, so two PRs each declaring their
    # own slug are individually valid. That is correct and must keep working.
    for slug, changed in (("alpha-feat", "packages/alpha/app.py"),
                          ("beta-feat", "packages/beta/app.py")):
        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t)
            write(root / changed, "z = 3\n")
            make_intent(root, "alpha-feat", ["packages/alpha/app.py"])
            make_intent(root, "beta-feat", ["packages/beta/app.py"])
            write(root / ".sdlc" / "version", "1\n")
            write(root / ".sdlc" / "active", f"{slug}\n")
            rc, out = run_gate(root, [changed])
            check(f"concurrent PR declaring '{slug}' validates independently",
                  rc == 0, out.strip()[-200:])

    # The real hazard is a LOST UPDATE, not a per-PR failure: .sdlc/active is a single
    # mutable file. PR B, cut before A merged, still carries active=B. With
    # strict=false (branches need not be up to date) B merges without rebasing and
    # overwrites the pointer, so A's attribution silently disappears from main.
    #
    # No gate check can prevent that -- each PR is individually correct, and the fix lives
    # in branch protection (require branches to be up to date), not in gate logic.
    #
    # What the gate CAN do is notice the operation that causes it: a PR whose own diff
    # rewrites .sdlc/active is performing a pointer handover. Flagging that makes the race
    # discoverable at review time instead of being folklore.
    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        write(root / "packages" / "alpha" / "app.py", "x = 1\n")
        make_intent(root, "alpha-feat", ["packages/alpha/app.py"])
        write(root / ".sdlc" / "version", "1\n")
        write(root / ".sdlc" / "active", "alpha-feat\n")

        # A PR that only changes source: no handover, so no concurrency note.
        rc, out = run_gate(root, ["packages/alpha/app.py"])
        check("no handover note when .sdlc/active is untouched",
              rc == 0 and "concurren" not in out.lower(), out.strip()[-200:])

        # A PR that rewrites the pointer: must still pass, but must SAY so.
        rc2, out2 = run_gate(root, ["packages/alpha/app.py", ".sdlc/active"])
        check("pointer handover still passes the gate", rc2 == 0, out2.strip()[-200:])
        check(
            "pointer handover is flagged as a concurrency hazard",
            "concurren" in out2.lower() or "up to date" in out2.lower(),
            f"got: {out2.strip()[-300:]}",
        )


def test_both_gates_agree() -> None:
    """The write-time hook and the merge-time gate must refuse the same thing.

    The hook is vendored per repository while the CI gate is the upstream copy, so drift
    between them is the failure mode that hurts most: the hook lets a developer write
    happily and CI refuses the merge later. Whatever the hook permits, the gate must permit.
    """
    print("both gates agree on multi-intent")
    hook = HERE / "sdlc_pretooluse_hook.py"
    if not hook.is_file():
        check("hook present", False, f"missing {hook}")
        return
    if os.name == "nt":
        # The hook is Python and portable, but this case shells nothing, so it runs
        # anywhere. Kept explicit in case that changes.
        pass

    with tempfile.TemporaryDirectory() as t:
        root = pathlib.Path(t)
        write(root / "src" / "a.py", "x = 1\n")
        make_intent(root, "alpha-feat", ["src/a.py"])
        make_intent(root, "beta-feat", ["src/b.py"])
        write(root / ".sdlc" / "version", "1\n")
        write(root / ".sdlc" / "active", "alpha-feat\nbeta-feat\n")

        payload = json.dumps({
            "hook_event_name": "preToolUse",
            "cwd": str(root),
            "tool_name": "fsWrite",
            "tool_input": {"path": "src/a.py", "content": "x = 2"},
        })
        p = subprocess.run([sys.executable, str(hook)], input=payload,
                           capture_output=True, text=True, cwd=str(root))
        out = p.stdout + p.stderr
        check("hook BLOCKS a multi-intent active pointer", p.returncode == 2,
              f"exit={p.returncode}: {out.strip()[-200:]}")
        check("hook says how many intents were declared", "2 intents" in out,
              f"got: {out.strip()[-200:]}")

        # And the CI gate refuses the same input, so the two cannot disagree.
        rc, gout = run_gate(root, ["src/a.py"])
        check("CI gate also refuses it", rc != 0, gout.strip()[-200:])
        check("both refusals cite the same rule (exactly one intent)",
              "one is allowed" in out and "one is allowed" in gout,
              "the two gates describe the rule differently")


def main() -> int:
    test_monorepo()
    test_concurrent()
    test_both_gates_agree()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} -> {FAILURES}")
        return 1
    print("all scale tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
