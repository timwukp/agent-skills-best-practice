#!/usr/bin/env python3
"""test_pretooluse_hook.py — prove the PreToolUse hook blocks and allows correctly.

Exit 0 = all pass. The hook's contract is exit 2 == BLOCK, exit 0 == ALLOW;
anything else is a warning that silently ALLOWS, so a test that only checked
"non-zero" would pass while the gate leaked. Each case asserts the EXACT code.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HOOK = pathlib.Path(__file__).resolve().parent / "sdlc_pretooluse_hook.py"
BLOCK, ALLOW = 2, 0


def run(event: dict) -> tuple[int, str]:
    p = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
    )
    return p.returncode, (p.stdout + p.stderr)


def mkrepo(tmp: pathlib.Path, *, sdlc: bool, active: str | None,
           statuses: dict[str, str] | None) -> pathlib.Path:
    root = tmp
    (root / ".git").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    if sdlc:
        (root / ".sdlc").mkdir(exist_ok=True)
        if active is not None:
            (root / ".sdlc" / "active").write_text(active + "\n", encoding="utf-8")
    if statuses:
        d = root / "intent" / (active or "slug")
        d.mkdir(parents=True, exist_ok=True)
        for name, st in statuses.items():
            (d / name).write_text(f"# t\n\n- **Status:** {st}\n", encoding="utf-8")
    return root


def ev(root: pathlib.Path, path: str, tool: str = "fs_write",
       event_name: str = "preToolUse") -> dict:
    # Default to the OFFICIAL camelCase spelling that real Kiro sends. The earlier
    # version of this test only ever sent PascalCase, which is why it passed while
    # the hook silently allowed everything under real Kiro.
    return {
        "hook_event_name": event_name,
        "cwd": str(root),
        "session_id": "test-session",
        "tool_name": tool,
        "tool_input": {"path": path, "content": "whatever"},
    }


def main() -> int:
    fails: list[str] = []

    def check(label: str, got: int, want: int, out: str = "") -> None:
        if got != want:
            fails.append(f"{label}: exit {got}, want {want} :: {out.strip()[:160]}")

    # 1. Non-write tool must never be gated.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="x", statuses=None)
        code, out = run(ev(root, "src/app.py", tool="read"))
        check("read tool is not gated", code, ALLOW, out)

    # 2. Repo without .sdlc/ is inert (must not break other projects).
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=False, active=None, statuses=None)
        code, out = run(ev(root, "src/app.py"))
        check("no .sdlc means inert", code, ALLOW, out)

    # 3. Opted in but no active slug -> BLOCK.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active=None, statuses=None)
        code, out = run(ev(root, "src/app.py"))
        check("no active slug blocks", code, BLOCK, out)

    # 4. Active slug but no intent dir -> BLOCK.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat", statuses=None)
        code, out = run(ev(root, "src/app.py"))
        check("missing intent dir blocks", code, BLOCK, out)

    # 5. intent accepted but spec still draft -> BLOCK (the real gate condition).
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "accepted", "spec.md": "draft"})
        code, out = run(ev(root, "src/app.py"))
        check("draft spec blocks build", code, BLOCK, out)

    # 6. Full chain accepted -> ALLOW.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "accepted", "spec.md": "signed-off",
                                "plan.md": "accepted"})
        code, out = run(ev(root, "src/app.py"))
        check("accepted chain allows", code, ALLOW, out)

    # 7. The artifacts themselves are always writable, even with nothing accepted,
    #    otherwise a change could never be started.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat", statuses=None)
        for p in ("intent/feat/intent.md", "intent/feat/spec.md", ".sdlc/active",
                  "evals/check.py", ".github/workflows/ci.yml"):
            code, out = run(ev(root, p))
            check(f"artifact '{p}' is writable", code, ALLOW, out)

    # 8. Unparsable stdin must ALLOW (fail open), not crash into a warning.
    p = subprocess.run([sys.executable, str(HOOK)], input="not json",
                       capture_output=True, text=True)
    check("unparsable event allows", p.returncode, ALLOW, p.stdout + p.stderr)

    # 9. A write with no discoverable path must ALLOW rather than guess.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat", statuses=None)
        code, out = run({"hook_event_name": "PreToolUse", "cwd": str(root),
                         "tool_name": "fs_write", "tool_input": {"content": "no path here"}})
        check("no path allows", code, ALLOW, out)

    # 10. A different hook event must be ignored.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat", statuses=None)
        code, out = run({"hook_event_name": "Stop", "cwd": str(root),
                         "tool_name": "fs_write", "tool_input": {"path": "src/app.py"}})
        check("non-PreToolUse event ignored", code, ALLOW, out)

    # 11. BOTH event-name spellings must gate. Real Kiro sends camelCase
    #     "preToolUse"; KiroCrew's ScriptHook sends PascalCase "PreToolUse". A hook
    #     that only recognises one silently allows everything on the other runtime,
    #     which is exactly the bug this case exists to catch.
    for spelling in ("preToolUse", "PreToolUse", "pretooluse"):
        with tempfile.TemporaryDirectory() as t:
            root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                          statuses={"intent.md": "accepted", "spec.md": "draft"})
            code, out = run(ev(root, "src/app.py", event_name=spelling))
            check(f"spelling '{spelling}' still blocks", code, BLOCK, out)

    # 12. An unrelated event name must NOT be treated as PreToolUse.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat", statuses=None)
        code, out = run(ev(root, "src/app.py", event_name="postToolUse"))
        check("postToolUse is not gated", code, ALLOW, out)

    # 13. MCP-style namespaced tool name that is a write tool still gates.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "accepted", "spec.md": "draft"})
        code, out = run(ev(root, "src/app.py", tool="@fs/write"))
        check("namespaced write tool blocks", code, BLOCK, out)

    # ---- gaps this section was written to expose -----------------------------

    # 14. An ABSOLUTE path in tool_input must still be gated. Tools commonly pass
    #     absolute paths, and a gate that only understands relative ones is inert
    #     in exactly the common case.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "accepted", "spec.md": "draft"})
        code, out = run({
            "hook_event_name": "preToolUse", "cwd": str(root), "tool_name": "fs_write",
            "tool_input": {"path": str(root / "src" / "app.py"), "content": "x"},
        })
        check("absolute path is gated", code, BLOCK, out)

    # 15. A file NESTED deeper than the repo root must resolve to the same repo.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "accepted", "spec.md": "draft"})
        (root / "src" / "deep" / "deeper").mkdir(parents=True, exist_ok=True)
        code, out = run(ev(root, "src/deep/deeper/x.py"))
        check("deeply nested path is gated", code, BLOCK, out)

    # 16. The status match must be whole-token and case-insensitive here too,
    #     via the gate the hook delegates to.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "Accepted", "spec.md": "Signed-Off",
                                "plan.md": "accepted by the tech lead"})
        code, out = run(ev(root, "src/app.py"))
        check("mixed-case statuses with detail allow", code, ALLOW, out)
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "not-accepted", "spec.md": "signed-off",
                                "plan.md": "accepted"})
        code, out = run(ev(root, "src/app.py"))
        check("'not-accepted' intent must block", code, BLOCK, out)

    # 17. .sdlc/active with surrounding whitespace / a trailing comment line must
    #     still resolve to the slug. Two cases, because a BLOCK result cannot tell
    #     "stripped correctly then blocked by the gate" apart from "did not strip,
    #     so the intent dir was not found" — both block. Only the ALLOW case
    #     discriminates.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active=None, statuses=None)
        (root / ".sdlc").mkdir(exist_ok=True)
        (root / ".sdlc" / "active").write_text("  feat  \n# a note\n", encoding="utf-8")
        d = root / "intent" / "feat"
        d.mkdir(parents=True, exist_ok=True)
        (d / "intent.md").write_text("# i\n\n- **Status:** accepted\n", encoding="utf-8")
        (d / "spec.md").write_text("# s\n\n- **Status:** draft\n", encoding="utf-8")
        code, out = run(ev(root, "src/app.py"))
        check("whitespace-padded active slug resolves and blocks", code, BLOCK, out)
    with tempfile.TemporaryDirectory() as t:
        # Same padding, but a FULLY accepted chain: this must ALLOW. If the slug is
        # not stripped the intent dir is never found and the hook blocks instead,
        # so this case fails the moment stripping is removed.
        root = mkrepo(pathlib.Path(t), sdlc=True, active=None, statuses=None)
        (root / ".sdlc").mkdir(exist_ok=True)
        (root / ".sdlc" / "active").write_text("\tfeat \n", encoding="utf-8")
        d = root / "intent" / "feat"
        d.mkdir(parents=True, exist_ok=True)
        (d / "intent.md").write_text("# i\n\n- **Status:** accepted\n", encoding="utf-8")
        (d / "spec.md").write_text("# s\n\n- **Status:** signed-off\n", encoding="utf-8")
        (d / "plan.md").write_text("# p\n\n- **Status:** accepted\n", encoding="utf-8")
        code, out = run(ev(root, "src/app.py"))
        check("whitespace-padded slug with accepted chain ALLOWS", code, ALLOW, out)

    # 18. A write touching BOTH an exempt artifact and a gated source file must
    #     block — the gated one decides, not whichever happens to be scanned first.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="feat",
                      statuses={"intent.md": "accepted", "spec.md": "draft"})
        code, out = run({
            "hook_event_name": "preToolUse", "cwd": str(root), "tool_name": "fs_write",
            "tool_input": {"paths": ["intent/feat/intent.md", "src/app.py"]},
        })
        check("mixed exempt+gated write blocks", code, BLOCK, out)

    # 19. An empty .sdlc/active (opted in but nothing declared) must block.
    with tempfile.TemporaryDirectory() as t:
        root = mkrepo(pathlib.Path(t), sdlc=True, active="", statuses=None)
        code, out = run(ev(root, "src/app.py"))
        check("empty active slug blocks", code, BLOCK, out)

    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        return 1
    print("all PreToolUse hook tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
