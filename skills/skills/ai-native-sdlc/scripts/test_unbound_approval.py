#!/usr/bin/env python3
"""test_unbound_approval.py — an accepted chain must not bless later, unrelated changes.

Written BEFORE the implementation.

THE DEFECT, found by using the mechanism rather than reading it. After a chain is
accepted and merged, `.sdlc/active` still points at it and its plan.md still names
the files it touched. The gate asks "is there an accepted chain naming this file?"
and never "does that acceptance cover THIS change". So the next change to any file
that plan named passes with no new approval — the signature outlives the diff it
signed.

Observed live on timwukp/Kiro-Crew-Training: a provenance fix to index.html passed
under intent/memory-internals, whose chain had been signed for a completely
different change (correcting memory-layer figures). The gate printed:

    note: 1 source file(s) changed, all named in intent/memory-internals/plan.md
    SDLC CI GATE PASSED

THE CONTRACT UNDER TEST. A completed intent reaches a TERMINAL status, `shipped`,
and a terminal intent cannot be the active one. The author must open a new intent
for a new change.

WHY THE OBVIOUS ASSERTION IS NOT ENOUGH. `satisfies()` is whole-token, so the
token `shipped` already fails to satisfy `accepted` — meaning "does the gate
refuse?" (U1) ALREADY passes today, for the wrong reason: the gate refuses while
believing the chain is merely unfinished. Its message then reads "does not have a
fully accepted chain", which is precisely the WRONG advice: it invites the author
to flip a spent intent back to `accepted` and carry on reusing it, which is the
defect. So the discriminating assertion is U2, on the message.

That is the same trap recorded in the threat model: a check whose condition is
looser than the requirement passes silently.

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
GATE = HERE / "sdlc_gate.py"
HOOK = HERE / "sdlc_pretooluse_hook.py"
PASS, VIOLATION = 0, 1
ALLOW, BLOCK = 0, 2

fails: list[str] = []


def check(label: str, got: int, want: int, out: str = "") -> None:
    if got != want:
        fails.append(f"{label}: exit {got}, want {want} :: {out.strip()[:200]}")


def want_in(label: str, needle: str, haystack: str) -> None:
    if needle.casefold() not in haystack.casefold():
        fails.append(f"{label}: expected {needle!r} in output :: {haystack.strip()[:300]}")


def want_not_in(label: str, needle: str, haystack: str) -> None:
    if needle.casefold() in haystack.casefold():
        fails.append(f"{label}: {needle!r} must NOT appear :: {haystack.strip()[:300]}")


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
           intent_status: str = "accepted", spec_status: str = "signed-off",
           plan_status: str = "accepted", accepted_for: str | None = None,
           author: str = "alice", accepted_by: str = "bob") -> pathlib.Path:
    """Same shape as test_hardening.mkrepo, with statuses and the binding added."""
    (root / ".git").mkdir(parents=True, exist_ok=True)
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "src" / "app.py").write_text("x = 1\n", encoding="utf-8")
    (root / ".sdlc").mkdir(parents=True, exist_ok=True)
    (root / ".sdlc" / "active").write_text(slug + "\n", encoding="utf-8")
    d = root / "intent" / slug
    d.mkdir(parents=True, exist_ok=True)
    bind = f"- **Accepted-for:** {accepted_for}\n" if accepted_for else ""
    (d / "intent.md").write_text(
        f"# i\n\n- **Author:** {author}\n- **Accepted-by:** {accepted_by}\n"
        f"- **Status:** {intent_status}\n", encoding="utf-8")
    (d / "spec.md").write_text(
        f"# s\n\n- **Author:** {author}\n- **Accepted-by:** {accepted_by}\n"
        f"- **Status:** {spec_status}\n", encoding="utf-8")
    listed = "\n".join(f"1. `{f}` — reason" for f in (plan_files or ["src/app.py"]))
    (d / "plan.md").write_text(
        f"# p\n\n- **Author:** {author}\n- **Accepted-by:** {accepted_by}\n"
        f"{bind}- **Status:** {plan_status}\n\n"
        f"## Files changed (in order of work)\n{listed}\n",
        encoding="utf-8")
    return root


def changed(root: pathlib.Path, *paths: str) -> str:
    f = root / "changed.txt"
    f.write_text("\n".join(paths) + "\n", encoding="utf-8")
    return str(f)


# ---- U0 baseline: a live, accepted chain still passes ------------------------
# Guards against "fix" by refusing everything.
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"])
    code, out = ci(r, "--require-active", "--changed-files-from", changed(r, "src/app.py"))
    check("U0 an accepted, un-shipped chain still passes", code, PASS, out)


# ---- U1 a shipped intent cannot be the active one ---------------------------
# NOTE: expected to pass ALREADY, for the wrong reason (see module docstring).
# Kept as a floor, not as the discriminator.
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"],
               intent_status="shipped", spec_status="shipped", plan_status="shipped")
    code, out = ci(r, "--require-active", "--changed-files-from", changed(r, "src/app.py"))
    check("U1 a shipped chain must not authorise a change", code, VIOLATION, out)


# ---- U2 THE DISCRIMINATOR: the refusal must name the right fix --------------
# A spent intent is not an unfinished one. Telling the author it "does not have a
# fully accepted chain" points them at flipping it back to accepted and reusing
# it -- the defect. The message must say the intent is complete and that a NEW
# intent is required.
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"],
               intent_status="shipped", spec_status="shipped", plan_status="shipped")
    _, out = ci(r, "--require-active", "--changed-files-from", changed(r, "src/app.py"))
    want_in("U2 refusal names the terminal state", "shipped", out)
    want_in("U2 refusal tells the author to open a new intent", "new intent", out)
    want_not_in("U2 refusal must not advise accepting the spent chain",
                "does not have a fully accepted chain", out)


# ---- U3 a terminal status must not satisfy an approval requirement ----------
# Asserted directly against BOTH implementations, because the CI gate is vendored
# and cannot import the local one -- drift between them is the worst failure mode.
sys.path.insert(0, str(HERE))
try:
    import sdlc_ci_gate as _ci
    import sdlc_gate as _local
except Exception as exc:  # pragma: no cover
    fails.append(f"U3 could not import both gates: {exc}")
else:
    # The two matchers are deliberately named differently (the CI gate is vendored
    # and standalone); test_ci_gate.py pins their agreement on a 14-row table.
    matchers = (("ci gate", _ci.satisfies), ("local gate", _local.status_satisfies))
    for name, satisfies in matchers:
        if satisfies("shipped", "accepted"):
            fails.append(f"U3 {name}: 'shipped' must NOT satisfy 'accepted'")
        if not satisfies("accepted", "accepted"):
            fails.append(f"U3 {name}: positive control failed — 'accepted' must satisfy")
    for name, mod in (("ci gate", _ci), ("local gate", _local)):
        if not hasattr(mod, "SHIPPED"):
            fails.append(f"U3 {name}: no SHIPPED terminal-status constant")
        elif mod.SHIPPED != "shipped":
            fails.append(f"U3 {name}: SHIPPED is {mod.SHIPPED!r}, want 'shipped'")


# ---- U4 the write-time hook must agree with the CI gate --------------------
# If the hook still allows writes under a spent intent, the developer works
# happily and CI refuses the merge later -- the drift failure mode.
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"],
               intent_status="shipped", spec_status="shipped", plan_status="shipped")
    code, out = hook(r, str(r / "src" / "app.py"))
    check("U4 hook blocks a write under a shipped intent", code, BLOCK, out)
    # "Does it block?" alone is NOT enough here, and this is the same trap U2 exists
    # for: the hook blocked even before this change, because `shipped` happens not to
    # satisfy `accepted`. It blocked while telling the author to "get it accepted" --
    # advice that performs the defect. So assert the REASON, and assert the
    # contradicting advice is gone.
    want_in("U4 hook names the terminal state", "shipped", out)
    want_not_in("U4 hook must not tell the author to accept a spent intent",
                "get it accepted", out)
    # Assert the LOCAL gate's own message too, not only what reaches it through the
    # hook. Found by a surviving mutation: disabling the gate's terminal branch left
    # this test green, because the gate's ordinary "status is 'shipped', need
    # 'accepted'" problem line is enough for the hook to suppress its generic advice.
    # So the hook's behaviour masked the gate's -- the assertion has to go direct.
    p = subprocess.run(
        [sys.executable, str(HERE / "sdlc_gate.py"), str(r / "intent" / "feat"), "build"],
        capture_output=True, text=True,
    )
    gout = p.stdout + p.stderr
    check("U4b local gate closes on a shipped intent", p.returncode, BLOCK, gout)
    want_in("U4b local gate tells the author to open a new intent", "new intent", gout)
    want_not_in("U4b local gate must not advise accepting the prior artifact",
                "Produce/accept the prior artifact", gout)

# All three copies of the terminal constant must agree. The hook is standalone (it
# subprocesses the gate), so nothing but a test stops the three drifting apart.
sys.path.insert(0, str(HERE))
try:
    import sdlc_ci_gate as _c
    import sdlc_gate as _g
    import sdlc_pretooluse_hook as _h
except Exception as exc:  # pragma: no cover
    fails.append(f"U4 could not import all three copies: {exc}")
else:
    got = {"ci gate": _c.SHIPPED, "local gate": _g.SHIPPED, "hook": _h.SHIPPED}
    if len(set(got.values())) != 1:
        fails.append(f"U4 SHIPPED disagrees across copies: {got}")


# ---- Accepted-for: bind the approval to the base it was granted against -----
# `shipped` (U1-U4) only stops a SPENT intent being reused. It does not stop an
# author flipping a status back, so it is honour-based like separation of duties.
# The real binding records WHAT the approval covered. Contract:
#   * plan.md may carry `- **Accepted-for:** <base-sha>`
#   * CI supplies the actual base via --base-sha (git merge-base origin/main HEAD)
#   * present + mismatch  -> REFUSE, naming the mismatch
#   * present + match     -> pass
#   * absent              -> pass, but WARN loudly with the enforcement version
#   * --base-sha omitted  -> pass, but SAY the binding was not verified
# The last two matter: a gate that quietly skips a check it advertises is the
# "weak pass" failure mode, so not-checked must be visible in the output.
BASE = "a" * 40
OTHER = "b" * 40

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"], accepted_for=BASE)
    code, out = ci(r, "--require-active", "--base-sha", BASE,
                   "--changed-files-from", changed(r, "src/app.py"))
    check("U5 Accepted-for matching the real base passes", code, PASS, out)

with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"], accepted_for=OTHER)
    code, out = ci(r, "--require-active", "--base-sha", BASE,
                   "--changed-files-from", changed(r, "src/app.py"))
    check("U6 Accepted-for for a DIFFERENT base is refused", code, VIOLATION, out)
    want_in("U6 refusal names the binding", "accepted-for", out)

with tempfile.TemporaryDirectory() as t:
    # No binding recorded: allowed during the deprecation window, but the output
    # must say so -- silence here would make the whole feature unfalsifiable.
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"])
    code, out = ci(r, "--require-active", "--base-sha", BASE,
                   "--changed-files-from", changed(r, "src/app.py"))
    check("U7 a missing binding still passes for now", code, PASS, out)
    want_in("U7 but warns that it will be enforced", "accepted-for", out)

with tempfile.TemporaryDirectory() as t:
    # Binding recorded but CI did not supply a base: must NOT look like a pass
    # that verified something. Same class as the 'Not enforced here' weak pass.
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"], accepted_for=BASE)
    code, out = ci(r, "--require-active",
                   "--changed-files-from", changed(r, "src/app.py"))
    check("U8 no --base-sha still passes", code, PASS, out)
    want_in("U8 but says the binding was not verified", "not verified", out)


print("unbound-approval:", "FAIL" if fails else "all pass")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
