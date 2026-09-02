#!/usr/bin/env python3
"""sdlc_pretooluse_hook.py — turn the AI-Native SDLC gate from ADVISORY into ENFORCED.

Registered as a KiroCrew **PreToolUse** script hook. KiroCrew feeds the hook event
as JSON on STDIN (Kiro-CLI-compatible) with at least:

    {"hook_event_name": "PreToolUse", "cwd": "...",
     "tool_name": "...", "tool_input": {...}}

Exit code contract (KiroCrew ScriptHook):
    0 = allow
    2 = BLOCK the tool; stderr is shown to the model
    other = warning only (does NOT block)

So every refusal path here must exit exactly 2, and every "not my business" path
must exit 0. A crash would exit 1 = warning = silently allow, therefore the whole
body is wrapped and any internal error is converted to an explicit allow with a
warning on stderr. Failing OPEN is deliberate: a buggy gate must not brick the
user's ability to edit files. The CI gate is the fail-closed backstop.

--- How it decides ---------------------------------------------------------------
The repo names its CURRENT change in a pointer file:

    .sdlc/active        -> one line: the intent slug (e.g. "quality-pass")

Artifacts live in   intent/<slug>/{intent,spec,plan}.md   (the skill's layout).

A write to a SOURCE file is allowed only when `plan.md` for the active slug is
accepted -- i.e. the Build gate is open. Writes to the artifacts themselves, and
to anything listed in `.sdlc/allow`, are always permitted, otherwise you could
never start a change.

If a repo has no `.sdlc/` directory the hook is inert (exit 0): this must not
break every other project on the machine.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys

# Tools that can modify files. Matched case-insensitively as substrings against
# the tool name, because the title grammar varies ("fs_write", "Creating x.py",
# "Editing x.py"). The hooks.json `matcher` narrows this further.
WRITE_TOOL_HINTS = ("fs_write", "write", "edit", "creating", "editing", "str_replace", "insert")

# Never gate these: they ARE the SDLC artifacts, or repo metadata you need in
# order to declare intent in the first place.
ALWAYS_ALLOW_SUFFIXES = ("intent.md", "spec.md", "plan.md", "REVIEW.md", "bands.yaml")
ALWAYS_ALLOW_DIRS = (".sdlc", "intent", "evals", ".github")

GATE = pathlib.Path(__file__).resolve().parent / "sdlc_gate.py"


def allow(msg: str = "") -> None:
    if msg:
        print(msg)
    sys.exit(0)


def block(reason: str) -> None:
    # stderr is what the model reads back, so it must say what to do next.
    print(reason, file=sys.stderr)
    sys.exit(2)


def find_repo_root(start: pathlib.Path) -> pathlib.Path | None:
    for p in [start, *start.parents]:
        if (p / ".git").exists() or (p / ".sdlc").is_dir():
            return p
    return None


def target_paths(tool_input: object) -> list[str]:
    """Pull plausible file paths out of an arbitrary tool_input blob."""
    found: list[str] = []

    def walk(v: object) -> None:
        if isinstance(v, str):
            if "/" in v or v.endswith((".py", ".md", ".html", ".js", ".ts", ".yaml", ".yml")):
                found.append(v)
        elif isinstance(v, dict):
            for k, sub in v.items():
                # 'content' is the file body, not a path -- skip it or we scan
                # the whole payload and match noise.
                if k in ("content", "new_str", "old_str", "newStr", "oldStr", "text"):
                    continue
                walk(sub)
        elif isinstance(v, (list, tuple)):
            for sub in v:
                walk(sub)

    walk(tool_input)
    return found


def is_exempt(path: str) -> bool:
    p = path.replace("\\", "/")
    if p.endswith(ALWAYS_ALLOW_SUFFIXES):
        return True
    parts = [seg for seg in p.split("/") if seg]
    return any(seg in ALWAYS_ALLOW_DIRS for seg in parts)


def main() -> None:
    raw = sys.stdin.read() or "{}"
    try:
        event = json.loads(raw)
    except Exception:
        allow()  # unparsable event is not the user's fault

    # The TRIGGER name in .kiro/hooks/*.json is PascalCase ("PreToolUse"), but the
    # STDIN payload's hook_event_name is camelCase ("preToolUse") -- the official
    # docs show "preToolUse" and "agentSpawn". KiroCrew's own ScriptHook path
    # instead passes its PascalCase event constant. Accept BOTH, casefolded, or the
    # gate silently allows everything on one of the two runtimes.
    if str(event.get("hook_event_name") or "").casefold() != "pretooluse":
        allow()

    tool_name = str(event.get("tool_name") or "")
    low = tool_name.lower()
    if not any(h in low for h in WRITE_TOOL_HINTS):
        allow()  # not a write tool

    paths = target_paths(event.get("tool_input"))
    if not paths:
        allow()  # cannot tell what it writes -> do not guess, do not block

    cwd = pathlib.Path(str(event.get("cwd") or os.getcwd()))

    for raw_path in paths:
        cand = pathlib.Path(raw_path)
        abs_path = cand if cand.is_absolute() else (cwd / cand)
        root = find_repo_root(abs_path.parent if abs_path.parent.exists() else cwd)
        if root is None:
            continue
        sdlc_dir = root / ".sdlc"
        if not sdlc_dir.is_dir():
            continue  # repo has not opted in -> inert

        try:
            rel = str(abs_path.resolve().relative_to(root.resolve()))
        except Exception:
            rel = raw_path
        if is_exempt(rel):
            continue

        active_file = sdlc_dir / "active"
        if not active_file.is_file() or not active_file.read_text(encoding="utf-8").strip():
            block(
                f"SDLC GATE: blocked write to '{rel}'.\n"
                f"No active change is declared. Create {root.name}/.sdlc/active containing the\n"
                "intent slug, and produce intent/<slug>/intent.md before writing source files."
            )

        slug = active_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        # A slug names a directory under intent/. Reject anything that could escape
        # the repo: `root/intent/..` resolves back to root and would look like a
        # valid intent dir, and pathlib lets an absolute part ("/etc") discard the
        # prefix entirely. Both were real traversals.
        if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", slug) or slug in (".", ".."):
            block(
                f"SDLC GATE: blocked write to '{rel}'.\n"
                f".sdlc/active contains {slug!r}, which is not a plain directory name.\n"
                "Use letters, digits, dot, underscore or hyphen — no '/', '\\' or '..'."
            )
        intent_dir = root / "intent" / slug
        if not intent_dir.is_dir():
            block(
                f"SDLC GATE: blocked write to '{rel}'.\n"
                f"Active slug is '{slug}' but intent/{slug}/ does not exist.\n"
                "Create intent.md (Stage 1) and spec.md (Stage 2) first."
            )

        # Delegate the actual decision to the tested gate.
        proc = subprocess.run(
            [sys.executable, str(GATE), str(intent_dir), "build"],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 2:
            detail = (proc.stderr or "").strip()
            block(
                f"SDLC GATE: blocked write to '{rel}'.\n"
                f"{detail}\n"
                "Advance the prior stage (and get it accepted) before writing code."
            )
        if proc.returncode not in (0, 2):
            allow(f"sdlc gate inconclusive (exit {proc.returncode}); allowing")

    allow()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # fail OPEN, loudly
        print(f"sdlc hook internal error, allowing: {exc}", file=sys.stderr)
        sys.exit(0)
