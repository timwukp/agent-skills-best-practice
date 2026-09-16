#!/usr/bin/env python3
"""test_claude_hook_config.py — tests the SHIPPED templates/claude-code-hooks/settings.json.

Written test-FIRST (this file was committed before the template existed, and observed
failing), mirroring test_hook_config.py for the Kiro template. Same hook script, second
runtime: Claude Code reads `hooks.PreToolUse[].hooks[].command` from settings.json, feeds
the event as JSON on stdin, and applies a STRICTER exit contract than Kiro:

    0     = allow
    2     = BLOCK the tool; stderr is shown to the model
    other = non-blocking warning (shown to the user, the tool still runs)

Two consequences are asserted here and nowhere else:

  * a refusal must exit EXACTLY 2 — under Kiro any non-zero blocks, so a gate that
    exits 1 on refusal would work in Kiro and silently allow in Claude Code;
  * fail-open costs less on this surface: an infrastructure failure that exits
    non-zero-non-2 is a warning, not a bricked repo. The self-disable paths are still
    asserted to exit 0, because the two templates share one command string and Kiro
    blocks on any non-zero.

The gate is planted under $HOME/.claude/skills/ai-native-sdlc/scripts — the resolver leg
the Kiro suite never exercises.

Exit 0 = all pass.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
CONFIG = SKILL / "templates" / "claude-code-hooks" / "settings.json"

BLOCK = 2  # Claude Code blocks ONLY on exit 2
ALLOW = 0


def load_command() -> str:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    pre = data["hooks"]["PreToolUse"]
    assert len(pre) == 1, "expected exactly one PreToolUse matcher entry"
    entry = pre[0]
    matcher = entry["matcher"]
    # The matcher is a regex over Claude Code tool names. It must catch the write
    # tools and must NOT catch read/exec tools -- a gate on Read would block the
    # agent from even looking at the repo it is refused from editing.
    for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        assert re.search(matcher, tool), f"matcher must match write tool {tool!r}"
    for tool in ("Read", "Bash", "Glob", "Grep"):
        assert not re.search(matcher, tool), f"matcher must NOT match {tool!r}"
    hooks = entry["hooks"]
    assert len(hooks) == 1, "expected exactly one command hook"
    h = hooks[0]
    assert h["type"] == "command"
    assert int(h["timeout"]) > 0, "a command hook needs a positive timeout"
    return h["command"]


def kiro_command() -> str:
    data = json.loads(
        (SKILL / "templates" / "kiro-hooks" / "sdlc-gate.json").read_text(encoding="utf-8"))
    return data["hooks"][0]["action"]["command"]


def mkrepo(tmp: pathlib.Path, spec_status: str | None) -> pathlib.Path:
    (tmp / ".git").mkdir(parents=True, exist_ok=True)
    (tmp / "src").mkdir(parents=True, exist_ok=True)
    (tmp / ".sdlc").mkdir(parents=True, exist_ok=True)
    (tmp / ".sdlc" / "active").write_text("feat\n", encoding="utf-8")
    d = tmp / "intent" / "feat"
    d.mkdir(parents=True, exist_ok=True)
    (d / "intent.md").write_text("# i\n\n- **Status:** accepted\n", encoding="utf-8")
    if spec_status:
        (d / "spec.md").write_text(f"# s\n\n- **Status:** {spec_status}\n", encoding="utf-8")
    return tmp


def run(cmd: str, repo: pathlib.Path, env: dict | None = None,
        cwd: pathlib.Path | None = None) -> int:
    """Run the hook command with a Claude Code-shaped PreToolUse event.

    Differences from the Kiro payload that are load-bearing: `hook_event_name` is
    PascalCase "PreToolUse" (Kiro CLI sends camelCase; the hook accepts both,
    casefolded), the tool is "Write" rather than "fs_write", and the path key is
    `file_path` rather than `path`.
    """
    payload = json.dumps({
        "hook_event_name": "PreToolUse",
        "session_id": "t",
        "transcript_path": "/tmp/t.jsonl",
        "cwd": str(repo),
        "tool_name": "Write",
        "tool_input": {"file_path": "src/app.py", "content": "y=2"},
    })
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(["/bin/sh", "-c", cmd], input=payload, capture_output=True,
                       text=True, env=e, cwd=str(cwd) if cwd else None)
    return p.returncode


def plant_gate(home: pathlib.Path) -> pathlib.Path:
    """Install the gate under a FAKE $HOME at the Claude Code resolution path."""
    dest = home / ".claude" / "skills" / "ai-native-sdlc" / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("sdlc_pretooluse_hook.py", "sdlc_gate.py"):
        shutil.copy2(HERE / name, dest / name)
    return dest


def main() -> int:
    fails: list[str] = []
    cmd = load_command()

    # ONE command string, TWO templates. The hook logic must not fork per runtime:
    # a fix applied to one template and not the other is exactly the drift the
    # single-source rule elsewhere in this repo exists to prevent.
    if cmd != kiro_command():
        fails.append("claude-code and kiro templates must ship the IDENTICAL command string")

    if "~/" in cmd:
        fails.append("command uses '~' — use \"$HOME\" so it survives a non-shell exec")

    # POSIX-only, same as the Kiro template and recorded as such in COMPATIBILITY.md.
    if os.name == "nt" or not pathlib.Path("/bin/sh").exists():
        print("  SKIP hook-command execution cases — no POSIX /bin/sh on this platform.")
        print("       The shipped hook command is POSIX-only (see COMPATIBILITY.md).")
        print("       Config-shape assertions above still ran.")
        if fails:
            print(f"FAIL ({len(fails)}):")
            for f in fails:
                print("  -", f)
            return 1
        print("all claude-code hook-config tests passed (execution cases skipped)")
        return 0

    # --- gate PRESENT: refusal must be exit 2 EXACTLY, not merely non-zero ----------
    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r1", "draft")
        code = run(cmd, repo, env={"HOME": str(home)}, cwd=repo)
        if code != BLOCK:
            fails.append(
                f"draft spec should BLOCK with exit 2 (Claude Code ignores other "
                f"non-zero codes), got {code}")

    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r2", "signed-off")
        (repo / "intent" / "feat" / "plan.md").write_text(
            "# p\n\n- **Status:** accepted\n", encoding="utf-8")
        code = run(cmd, repo, env={"HOME": str(home)}, cwd=repo)
        if code != ALLOW:
            fails.append(f"accepted chain should ALLOW (0), got {code}")

    # --- resolution ORDER: a repo-local copy must win over $HOME/.claude ------------
    # Under Claude Code the stub's exit 3 is a warning rather than a block; the
    # assertion is about WHICH script ran, and 3 proves it was the repo-local stub.
    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r3", "draft")
        local = repo / ".sdlc" / "scripts"
        local.mkdir(parents=True, exist_ok=True)
        (local / "sdlc_pretooluse_hook.py").write_text(
            "import sys\nsys.exit(3)\n", encoding="utf-8")
        code = run(cmd, repo, env={"HOME": str(home)}, cwd=repo)
        if code != 3:
            fails.append(
                f"repo-local .sdlc/scripts gate must take precedence over $HOME, got {code}")

    # --- infrastructure failures must NOT block ------------------------------------
    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r4", "draft")
        shonly = pathlib.Path(t) / "shonly"
        shonly.mkdir()
        sh = shutil.which("sh") or "/bin/sh"
        os.symlink(sh, shonly / "sh")
        code = run(cmd, repo, env={"PATH": str(shonly), "HOME": str(home)}, cwd=repo)
        if code != ALLOW:
            fails.append(f"missing python3 must SELF-DISABLE (0) not block, got {code}")

    with tempfile.TemporaryDirectory() as t:
        repo = mkrepo(pathlib.Path(t) / "r5", "draft")
        code = run(cmd, repo, env={"HOME": str(pathlib.Path(t) / "nohome")}, cwd=repo)
        if code != ALLOW:
            fails.append(f"missing gate script must SELF-DISABLE (0), got {code}")

    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        return 1
    print("all claude-code hook-config tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
