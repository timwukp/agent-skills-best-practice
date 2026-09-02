#!/usr/bin/env python3
"""mutation_proof.py — prove the test suites can actually FAIL.

A suite that has only ever been seen green is not evidence of anything: it may be
asserting nothing, or asserting the same wrong thing the code does. This applies a
list of deliberate MUTATIONS to each implementation, runs the matching suite
against the mutated copy, and requires the suite to go RED.

A mutation that leaves the suite green is reported as SURVIVED — an untested
behaviour, i.e. a real gap in the tests, not a pass.

Nothing here touches the real files: each mutation is applied to a copy in a temp
tree. Exit 0 = every mutation was killed.
"""

from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent

# (label, implementation file, suite file, find, replace)
MUTATIONS: list[tuple[str, str, str, str, str]] = [
    # --- sdlc_gate.py -------------------------------------------------------
    (
        "gate: substring match instead of whole-token (lets 'not-accepted' pass)",
        "sdlc_gate.py", "test_gate.py",
        "return needed.casefold() in status.casefold().split()",
        "return needed.casefold() in status.casefold()",
    ),
    (
        "gate: case-sensitive match (refuses 'Accepted')",
        "sdlc_gate.py", "test_gate.py",
        "return needed.casefold() in status.casefold().split()",
        "return needed in status.split()",
    ),
    (
        "gate: treat the unfilled template as a real status",
        "sdlc_gate.py", "test_gate.py",
        'if "|" in raw:\n        return "<unset-template>"',
        'if False:\n        return "<unset-template>"',
    ),
    (
        "gate: unknown stage silently allowed",
        "sdlc_gate.py", "test_gate.py",
        'print(f"unknown stage: {stage}", file=sys.stderr)\n        return 2',
        'print(f"unknown stage: {stage}", file=sys.stderr)\n        return 0',
    ),
    (
        "gate: missing file counts as satisfied",
        "sdlc_gate.py", "test_gate.py",
        'if not path.exists():\n        return "<missing>"',
        'if not path.exists():\n        return "accepted"',
    ),
    # --- sdlc_pretooluse_hook.py -------------------------------------------
    (
        "hook: only PascalCase event recognised (inert under real Kiro)",
        "sdlc_pretooluse_hook.py", "test_pretooluse_hook.py",
        'if str(event.get("hook_event_name") or "").casefold() != "pretooluse":',
        'if event.get("hook_event_name") != "PreToolUse":',
    ),
    (
        "hook: skip absolute paths entirely",
        "sdlc_pretooluse_hook.py", "test_pretooluse_hook.py",
        "        cand = pathlib.Path(raw_path)",
        "        cand = pathlib.Path(raw_path)\n        if cand.is_absolute():\n            continue",
    ),
    (
        "hook: stop after the first path (mixed exempt+gated write leaks)",
        "sdlc_pretooluse_hook.py", "test_pretooluse_hook.py",
        "    for raw_path in paths:",
        "    for raw_path in paths[:1]:",
    ),
    (
        "hook: do not strip the active slug",
        "sdlc_pretooluse_hook.py", "test_pretooluse_hook.py",
        'slug = active_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()',
        'slug = active_file.read_text(encoding="utf-8").splitlines()[0]',
    ),
    (
        "hook: block instead of allowing when the event is unparsable (fail closed)",
        "sdlc_pretooluse_hook.py", "test_pretooluse_hook.py",
        "    except Exception:\n        allow()  # unparsable event is not the user's fault",
        '    except Exception:\n        block("unparsable")',
    ),
    (
        "hook: treat a non-write tool as a write tool",
        "sdlc_pretooluse_hook.py", "test_pretooluse_hook.py",
        "    if not any(h in low for h in WRITE_TOOL_HINTS):\n        allow()  # not a write tool",
        "    if False:\n        allow()  # not a write tool",
    ),
    # --- sdlc_ci_gate.py ---------------------------------------------------
    (
        "ci: substring match instead of whole-token",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        "return needed.casefold() in status.casefold().split()",
        "return needed.casefold() in status.casefold()",
    ),
    (
        "ci: skip the ladder check for spec",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        "if satisfies(s_spec, SIGNED_OFF) and not satisfies(s_intent, ACCEPTED):",
        "if False:",
    ),
    (
        "ci: skip the ladder check for plan",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        "if satisfies(s_plan, ACCEPTED) and not satisfies(s_spec, SIGNED_OFF):",
        "if False:",
    ),
    (
        "ci: a missing changed-files list is silently ignored",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        'problems.append(f"changed-files list not found: {listing}")',
        'notes.append(f"changed-files list not found: {listing}")',
    ),
    (
        "ci: source change with no accepted chain is allowed",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        "if source_changed and not plan_accepted:",
        "if False:",
    ),
    (
        "ci: missing intent.md is not reported",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        'if s_intent == "<missing>":',
        "if False:",
    ),
    (
        "ci: template placeholder accepted",
        "sdlc_ci_gate.py", "test_ci_gate.py",
        'if st == "<unset-template>":',
        "if False:",
    ),
]


def main() -> int:
    killed, survived, broken = 0, [], []

    for label, impl, suite, find, repl in MUTATIONS:
        src_impl = HERE / impl
        src_suite = HERE / suite
        if not src_impl.is_file() or not src_suite.is_file():
            broken.append(f"{label}: missing {impl} or {suite}")
            continue

        with tempfile.TemporaryDirectory() as t:
            work = pathlib.Path(t) / "scripts"
            work.mkdir(parents=True)
            # Copy every script so imports and sibling lookups still resolve.
            for f in HERE.glob("*.py"):
                shutil.copy2(f, work / f.name)

            text = (work / impl).read_text(encoding="utf-8")
            if find not in text:
                broken.append(f"{label}: anchor not found in {impl} (mutation is stale)")
                continue
            (work / impl).write_text(text.replace(find, repl, 1), encoding="utf-8")

            r = subprocess.run(
                [sys.executable, str(work / suite)],
                capture_output=True, text=True, cwd=str(work),
            )
            if r.returncode != 0:
                killed += 1
                print(f"KILLED   {label}")
            else:
                survived.append(label)
                print(f"SURVIVED {label}")

    print()
    print(f"{killed} killed, {len(survived)} survived, {len(broken)} broken")
    if broken:
        print("\nBROKEN (fix the mutation list, it no longer matches the code):")
        for b in broken:
            print("  -", b)
    if survived:
        print("\nSURVIVED — these behaviours are NOT covered by any assertion:")
        for s in survived:
            print("  -", s)
    return 0 if (not survived and not broken) else 1


if __name__ == "__main__":
    raise SystemExit(main())
