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


def run(cmd: str, repo: pathlib.Path, env: dict | None = None,
        cwd: pathlib.Path | None = None) -> int:
    """Run the hook command.

    `cwd` is the PROCESS working directory and is distinct from the `cwd` field inside the
    JSON payload. That distinction is load-bearing: the command's resolution chain starts
    with the RELATIVE path ".sdlc/scripts/sdlc_pretooluse_hook.py", which resolves against
    the process CWD, while the payload's cwd is only what the hook reads to locate the repo.
    Kiro runs the hook from the workspace root, so tests pass cwd=repo to match production.
    """
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
                       text=True, env=e, cwd=str(cwd) if cwd else None)
    return p.returncode


def plant_gate(home: pathlib.Path) -> pathlib.Path:
    """Install the gate under a FAKE $HOME at one of the command's resolution paths.

    This is what makes the test hermetic. Previously cases 1 and 2 inherited the real
    $HOME, so they only exercised the gate when the developer happened to have the skill
    installed at ~/.kiro/skills/. On a clean machine (and in CI) the resolution chain found
    nothing, the command took its deliberate self-disable path, and:

      * "draft must BLOCK" FAILED  — the visible symptom, and
      * "accepted must ALLOW" PASSED FOR THE WRONG REASON — it got 0 from the self-disable,
        not from an accepted chain. A false pass is the worse of the two.

    The hook execs its sibling sdlc_gate.py, so both files must be planted.
    """
    dest = home / ".kiro" / "skills" / "ai-native-sdlc" / "scripts"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("sdlc_pretooluse_hook.py", "sdlc_gate.py"):
        shutil.copy2(HERE / name, dest / name)
    return dest


def main() -> int:
    fails: list[str] = []
    cmd = load_command()

    # The command must not rely on `~` expansion: it is not expanded by every
    # exec path, and an unexpanded path means "file not found".
    if "~/" in cmd:
        fails.append("command uses '~' — use \"$HOME\" so it survives a non-shell exec")

    # The shipped hook `command` is a POSIX `sh -c '...'` string: it uses [ -f ],
    # command -v and exec. Windows has no /bin/sh, so the EXECUTION cases below cannot
    # run there -- previously they raised FileNotFoundError (WinError 2) and failed the
    # whole matrix cell.
    #
    # This is a genuine scope limit, not a test shortcut: the local hook template is
    # POSIX-only and COMPATIBILITY.md records it as such. The gate SCRIPTS are pure
    # Python and are exercised on Windows by the other suites, so Windows loses only the
    # write-time hook, not the CI gate. The skip is printed loudly rather than silently
    # returning success.
    if os.name == "nt" or not pathlib.Path("/bin/sh").exists():
        print("  SKIP hook-command execution cases — no POSIX /bin/sh on this platform.")
        print("       The shipped hook command is POSIX-only (see COMPATIBILITY.md).")
        print("       Config-shape assertions above still ran.")
        if fails:
            print(f"FAIL ({len(fails)}):")
            for f in fails:
                print("  -", f)
            return 1
        print("all hook-config tests passed (execution cases skipped: non-POSIX host)")
        return 0

    # --- gate PRESENT: the decision must come from the artifact chain ----------------
    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r1", "draft")
        code = run(cmd, repo, env={"HOME": str(home)}, cwd=repo)
        if code < BLOCK_MIN:
            fails.append(f"draft spec should BLOCK (non-zero), got {code}")

    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r2", "signed-off")
        (repo / "intent" / "feat" / "plan.md").write_text(
            "# p\n\n- **Status:** accepted\n", encoding="utf-8")
        code = run(cmd, repo, env={"HOME": str(home)}, cwd=repo)
        if code != ALLOW:
            fails.append(f"accepted chain should ALLOW (0), got {code}")

    # --- resolution ORDER: a repo-local copy must win over $HOME --------------------
    # Documented behaviour that nothing asserted. A repo pinning its own vendored gate
    # must not be silently overridden by whatever the developer has installed.
    with tempfile.TemporaryDirectory() as t:
        home = pathlib.Path(t) / "home"
        plant_gate(home)
        repo = mkrepo(pathlib.Path(t) / "r3", "draft")
        local = repo / ".sdlc" / "scripts"
        local.mkdir(parents=True, exist_ok=True)
        # A repo-local stub with a distinctive exit code: if it runs, we see 3, which is
        # neither the gate's block (2) nor its allow (0).
        (local / "sdlc_pretooluse_hook.py").write_text(
            "import sys\nsys.exit(3)\n", encoding="utf-8")
        code = run(cmd, repo, env={"HOME": str(home)}, cwd=repo)
        if code != 3:
            fails.append(
                f"repo-local .sdlc/scripts gate must take precedence over $HOME, got {code}")

    # --- infrastructure failures must NOT block ------------------------------------
    # Each case plants the gate first, so exit 0 can ONLY be attributable to the
    # infrastructure condition under test and not to a missing gate.
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
            fails.append(
                f"missing python3 must SELF-DISABLE (0) not block, got {code}")

    # Missing gate script must not block either.
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
    print("all hook-config tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
