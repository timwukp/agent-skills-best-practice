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


BASE = "a" * 40
OTHER = "b" * 40

# ---- U0 baseline: a live, accepted and correctly-bound chain still passes ---
# Guards against "fix" by refusing everything.
with tempfile.TemporaryDirectory() as t:
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"], accepted_for=BASE)
    code, out = ci(r, "--require-active", "--base-sha", BASE,
                   "--changed-files-from", changed(r, "src/app.py"))
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
# The v2 binding contract is fail-closed:
#   * plan.md carries `- **Accepted-for:** <base-sha>`
#   * CI supplies the actual base via --base-sha (git merge-base origin/main HEAD)
#   * present + mismatch  -> REFUSE, naming the mismatch
#   * present + match     -> pass
#   * absent              -> REFUSE (the v1 deprecation window is over)
#   * --base-sha omitted  -> REFUSE (a misconfigured pipeline cannot claim binding)
#
# The final row is load-bearing. v1 made an unverifiable binding visible but still
# returned 0. That was appropriate for the announced compatibility window; keeping it
# in v2 would make enforcement optional at the exact layer that advertises it.

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
    # v1 warned and passed here under its announced compatibility window. v2 is the
    # version named in that announcement, so retaining the pass would publish a tag
    # that claims enforcement while running the warning-only implementation.
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"])
    code, out = ci(r, "--require-active", "--base-sha", BASE,
                   "--changed-files-from", changed(r, "src/app.py"))
    check("U7 v2 refuses a plan with no Accepted-for binding", code, VIOLATION, out)
    want_in("U7 refusal names the missing binding", "accepted-for", out)

with tempfile.TemporaryDirectory() as t:
    # A binding that the pipeline does not compare is not a control. v1 made the
    # omission visible while returning 0; v2 must fail closed so a workflow that
    # forgets --base-sha cannot silently downgrade the guarantee.
    r = mkrepo(pathlib.Path(t), "feat", plan_files=["src/app.py"], accepted_for=BASE)
    code, out = ci(r, "--require-active",
                   "--changed-files-from", changed(r, "src/app.py"))
    check("U8 v2 refuses when --base-sha is omitted", code, VIOLATION, out)
    want_in("U8 refusal says the binding was not verified", "not verified", out)

# ---- U9 the v2 identity, release history and wiring must all agree ---------
# A tag name does not change the bytes it points at. The executable must identify
# its own enforcement generation, otherwise `sdlc-gate-v2` could package the exact
# warning-only v1 implementation while the release page claims the deprecation ended.
try:
    import sdlc_ci_gate as _versioned_gate
except Exception as exc:  # pragma: no cover
    fails.append(f"U9 could not import the versioned gate: {exc}")
else:
    if getattr(_versioned_gate, "GATE_VERSION", None) != 2:
        fails.append(
            f"U9 gate identifies as version "
            f"{getattr(_versioned_gate, 'GATE_VERSION', '<missing>')!r}, want 2"
        )

# The old announcement remains in COMPATIBILITY.md as release HISTORY, and the
# workflow must actually pass the base. Documented-but-unwired is the
# "channel named in a doc but switched off" failure this project has hit before, so
# assert reachability rather than mere presence.
SKILL_ROOT = HERE.parent
compat = (SKILL_ROOT / "COMPATIBILITY.md").read_text(encoding="utf-8")
# Pin the ANNOUNCEMENT HEADING, not the mere presence of the words. A first draft
# asserted `"Accepted-for" in compat`, which two mutations survived: the term appears
# throughout the explanatory prose, so deleting the heading -- the part that actually
# constitutes the announcement -- left the assertion green. Weak-eval shape again.
heads = [ln for ln in compat.splitlines() if ln.lstrip().startswith("#")]
if not any("Accepted-for" in h and "sdlc-gate-v2" in h for h in heads):
    fails.append("U9 COMPATIBILITY.md has no heading announcing that Accepted-for "
                 "becomes required in sdlc-gate-v2")
if "ENFORCED IN `sdlc-gate-v2`" not in compat:
    fails.append("U9 the consumed deprecation is not recorded as enforced in v2")

wf = (SKILL_ROOT / "templates" / "github-workflows" / "sdlc-gate.yml").read_text(
    encoding="utf-8"
)
if "--base-sha" not in wf:
    fails.append("U9 the workflow template never passes --base-sha, so the binding "
                 "would never be verified in real use")
if "merge-base" not in wf:
    fails.append("U9 the workflow template must use merge-base, not the base tip: the "
                 "base moves after the branch is cut")

plan_tpl = (SKILL_ROOT / "templates" / "plan.md").read_text(encoding="utf-8")
# The FIELD LINE, not the term anywhere in the prose -- same reason as above.
if not any(
    ln.lstrip().startswith("- **Accepted-for:**") for ln in plan_tpl.splitlines()
):
    fails.append("U9 templates/plan.md has no '- **Accepted-for:**' field line, so no "
                 "author would know to record it")


print("unbound-approval:", "FAIL" if fails else "all pass")
for f in fails:
    print("  -", f)
sys.exit(1 if fails else 0)
