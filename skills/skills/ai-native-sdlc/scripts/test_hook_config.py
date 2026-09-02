#!/usr/bin/env python3
"""test_hook_config.py — tests the SHIPPED .kiro/hooks/sdlc-gate.json itself.

Written test-FIRST (before the config was proven), because the config's `command`
string is the part that actually runs in production and nothing covered it: the
hook script had tests, the shell wrapper around it had none.

Why this matters more than it looks: under Kiro's contract ANY non-zero exit from a
PreToolUse command BLOCKS the tool. So a missing interpreter, an unexpanded `~`, or
a missing script would not merely disable the gate -- it would block EVERY write in
the repo. Those infrastructure paths must exit 0, and that is what is asserted here.

Exit 0 = all pass.
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent
CONFIG = SKILL / "templates" / "kiro-hooks" / "sdlc-gate.json"

BLOCK_MIN = 1  # any non-zero blocks under official Kiro
ALLOW = 0


def load_command() -> str:
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    assert data["version"] == "v1", "config must declare schema version v1"
    hooks = data["hooks"]
    assert len(hooks) == 1, "expected exactly one hook"
    h = hooks[0]
    assert h["trigger"] == "PreToolUse", "trigger must be PascalCase PreToolUse"
    assert h["matcher"] == "write", "matcher should be the built-in 'write' category"
    assert h["action"]["type"] == "command"
    assert int(h["timeout"]) > 0, "a command action needs a positive timeout"
    return h["action"]["command"]


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


def run(cmd: str, repo: pathlib.Path, env: dict | None = None) -> int:
    payload = json.dumps({
        "hook_event_name": "preToolUse",
        "cwd": str(repo),
        "session_id": "t",
        "tool_name": "fs_write",
        "tool_input": {"path": "src/app.py", "content": "y=2"},
    })
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(["/bin/sh", "-c", cmd], input=payload, capture_output=True,
                       text=True, env=e)
    return p.returncode


def main() -> int:
    fails: list[str] = []
    cmd = load_command()

    # The command must not rely on `~` expansion: it is not expanded by every
    # exec path, and an unexpanded path means "file not found".
    if "~/" in cmd:
        fails.append("command uses '~' — use \"$HOME\" so it survives a non-shell exec")

    with tempfile.TemporaryDirectory() as t:
        repo = mkrepo(pathlib.Path(t), "draft")
        code = run(cmd, repo)
        if code < BLOCK_MIN:
            fails.append(f"draft spec should BLOCK (non-zero), got {code}")

    with tempfile.TemporaryDirectory() as t:
        repo = mkrepo(pathlib.Path(t), "signed-off")
        (repo / "intent" / "feat" / "plan.md").write_text(
            "# p\n\n- **Status:** accepted\n", encoding="utf-8")
        code = run(cmd, repo)
        if code != ALLOW:
            fails.append(f"accepted chain should ALLOW (0), got {code}")

    # Infrastructure failures must NOT block. A PATH with a shell but no python3.
    with tempfile.TemporaryDirectory() as t:
        repo = mkrepo(pathlib.Path(t), "draft")
        shonly = pathlib.Path(t) / "shonly"
        shonly.mkdir()
        sh = shutil.which("sh") or "/bin/sh"
        os.symlink(sh, shonly / "sh")
        code = run(cmd, repo, env={"PATH": str(shonly)})
        if code != ALLOW:
            fails.append(
                f"missing python3 must SELF-DISABLE (0) not block, got {code}")

    # Missing gate script must not block either.
    with tempfile.TemporaryDirectory() as t:
        repo = mkrepo(pathlib.Path(t), "draft")
        code = run(cmd, repo, env={"HOME": str(pathlib.Path(t) / "nohome")})
        if code != ALLOW:
            fails.append(f"missing gate script must SELF-DISABLE (0), got {code}")

    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print("  -", f)
        return 1
    print("all hook-config tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
