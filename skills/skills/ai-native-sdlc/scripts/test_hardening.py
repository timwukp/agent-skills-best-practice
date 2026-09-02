#!/usr/bin/env python3
"""test_hardening.py — tests for the batch-1 hardening of the SDLC gates.

Written BEFORE the implementation. Four behaviours, each a real defect found by
auditing the gates rather than by using them:

  H1  coverage must tie a changed file to the ACTIVE intent's plan, not merely to
      "some accepted chain exists somewhere in the repo". Once one intent was ever
      accepted, the old rule was permanently satisfied.
  H2  the artifact schema must be versioned, so a gate older than the repo refuses
      loudly instead of misreading it.
  H3  separation of duties must be an explicit attested claim (Author vs
      Accepted-by), not an honour-system sentence in the docs.
  H4  a slug from .sdlc/active must not be able to escape the repo. `../../etc`
      previously resolved through `root / "intent" / slug` — a path traversal.

Exit 0 = all pass.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
CI_GATE = HERE / "sdlc_ci_gate.py"
HOOK = HERE / "sdlc_pretooluse_hook.py"
PASS, VIOLATION = 0, 1
ALLOW, BLOCK = 0, 2

fails: list[str] = []


def check(label: str, got: int, want: int, out: str = "") -> None:
    if got != want:
        fails.append(f"{label}: exit {got}, want {want} :: {out.strip()[:200]}")


def ci(repo: pathlib.Path, *extra: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(CI_GATE), "--repo", str(repo), *extra],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def hook(repo: pathlib.Path, path: str) -> tuple[int, str]:
    payload = json.dumps({
        "hook_event_name": "preToolUse", "cwd": str(repo), "tool_name": "fs_write",
        "tool_input": {"path": path, "content": "x"},
    })
    p = subprocess.run([sys.executable, str(HOOK)], input=payload,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def mkrepo(root: pathlib.Path, slug: str, *, plan_files: list[str] | None = None,
           author: str = "alice", accepted_by: str = "bob",
           schema: str | None = None, active: str | None = None) -> pathlib.Path:
    (root / ".git").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (root / ".sdlc").mkdir(parents=True, exist_ok=True)
    (root / ".sdlc" / "active").write_text((active if active is not None else slug) + "\n",
                                           encoding="utf-8")
    if schema is not None:
        (root / ".sdlc" / "version").write_text(schema + "\n", encoding="utf-8")
    d = root / "intent" / slug
    d.mkdir(parents=True, exist_ok=True)
    (d / "intent.md").write_text(
        f"# i\n\n- **Author:** {author}\n- **Accepted-by:** {accepted_by}\n"
        f"- **Status:** accepted\n", encoding="utf-8")
    (d / "spec.md").write_text(
        f"# s\n\n- **Author:** {author}\n- **Accepted-by:** {accepted_by}\n"
        f"- **Status:** signed-off\n", encoding="utf-8")
    listed = "\n".join(f"1. `{f}` — reason" for f in (plan_files or ["src/app.py"]))
    (d / "plan.md").write_text(
        f"# p\n\n- **Author:** {author}\n- **Accepted-by:** {accepted_by}\n"
        f"- **Status:** accepted\n\n## Files changed (in order of work)\n{listed}\n",
        encoding="utf-8")
    return root


def changed(root: pathlib.Path, *paths: str) -> str:
    f = root / "changed.txt"
    f.write_text("\n".join(paths) + "\n", encoding="utf-8")
    return str(f)


# ---- H1: coverage must name the file in the ACTIVE intent's plan -------------
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"])
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H1 a file named in the active plan passes", code, PASS, out)

with tempfile.TemporaryDirectory() as t:
    # The chain is fully accepted, but it says nothing about the file being changed.
    # The OLD rule passed this because "an accepted chain exists".
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/other.py"])
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H1 a file NOT in the plan is a violation", code, VIOLATION, out)

with tempfile.TemporaryDirectory() as t:
    # A second, stale accepted intent must not launder an unrelated change.
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/other.py"])
    d = r / "intent" / "old-done"
    d.mkdir(parents=True)
    for n, s in (("intent.md", "accepted"), ("spec.md", "signed-off"), ("plan.md", "accepted")):
        (d / n).write_text(f"# x\n\n- **Author:** a\n- **Accepted-by:** b\n- **Status:** {s}\n",
                           encoding="utf-8")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H1 an unrelated accepted chain does not launder the change", code, VIOLATION, out)

# ---- H2: schema version --------------------------------------------------------
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", schema="1")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H2 a supported schema version passes", code, PASS, out)

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", schema="999")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H2 a NEWER schema than the gate supports is refused", code, VIOLATION, out)
    if "upgrade" not in out.lower() and "newer" not in out.lower():
        fails.append("H2 the refusal must tell the operator the gate is out of date")

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", schema="not-a-number")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H2 an unparsable schema version is refused", code, VIOLATION, out)

# ---- H3: separation of duties --------------------------------------------------
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", author="alice", accepted_by="alice")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H3 self-approval is a violation", code, VIOLATION, out)

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", author="Alice", accepted_by="  alice  ")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H3 self-approval detection ignores case and padding", code, VIOLATION, out)

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", accepted_by="")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H3 an accepted artifact with no approver is a violation", code, VIOLATION, out)

# ---- H4: slug path traversal ---------------------------------------------------
for evil in ("../../etc", "..", "a/../../b", "/etc", "feat/../..", "a\\..\\..\\b"):
    with tempfile.TemporaryDirectory() as t:
        r = mkrepo(pathlib.Path(t), "feat", active=evil)
        code, out = hook(r, "src/app.py")
        if code == ALLOW:
            fails.append(f"H4 traversal slug '{evil}' was ALLOWED through the hook")
        # Blocking is not enough: without the guard a slug like '..' resolves to the
        # repo root, which IS a directory, and the hook then blocks for the WRONG
        # reason (no artifacts there). Require the refusal to name the real cause,
        # or the guard can be deleted without any test noticing.
        elif "not a plain directory name" not in out:
            fails.append(
                f"H4 slug '{evil}' was blocked but NOT for being a traversal — "
                f"the guard may be absent. Message: {out.strip()[:120]}"
            )
        code, out = ci(r, "--require-active")
        if code == PASS:
            fails.append(f"H4 traversal slug '{evil}' passed the CI gate")
        elif "not a plain directory name" not in out and "traversal" not in out:
            fails.append(f"H4 CI gate blocked '{evil}' for the wrong reason: {out.strip()[:120]}")

# ---- H1b: an INCOMPLETE active chain must fail even when the plan names the file
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"])
    # Plan back to DRAFT. Chosen deliberately over breaking the spec: a draft spec
    # under an accepted plan also trips the LADDER rule, so that case cannot tell
    # the chain-completeness rule apart from the ladder rule. A draft PLAN trips no
    # ladder (nothing is accepted above it), so only completeness can catch it.
    (r / "intent" / "feat" / "plan.md").write_text(
        "# p\n\n- **Author:** alice\n- **Accepted-by:** bob\n- **Status:** draft\n\n"
        "## Files changed (in order of work)\n1. `src/app.py` — reason\n",
        encoding="utf-8")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H1b an incomplete active chain is a violation even if the plan lists the file",
          code, VIOLATION, out)
    if "does not have a fully accepted chain" not in out:
        fails.append(
            f"H1b blocked for the wrong reason — completeness rule may be absent: "
            f"{out.strip()[:140]}"
        )

# ---- H2b: an EMPTY status value must not be read as a real status ---------------
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat")
    (r / "intent" / "feat" / "intent.md").write_text(
        "# i\n\n- **Author:** alice\n- **Accepted-by:** bob\n- **Status:** \n",
        encoding="utf-8")
    code, out = ci(r, "--changed-files-from", changed(r, "src/app.py"))
    check("H2b an empty Status is not a valid status", code, VIOLATION, out)

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat")
    code, out = hook(r, "src/app.py")
    check("H4 a normal slug still works after the traversal guard", code, ALLOW, out)

if fails:
    print(f"FAIL ({len(fails)}):")
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("all hardening tests passed")
