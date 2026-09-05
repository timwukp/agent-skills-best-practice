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
        'ln.strip()\n            for ln in active_file.read_text(encoding="utf-8").splitlines()\n            if ln.strip() and not ln.strip().startswith("#")',
        'ln\n            for ln in active_file.read_text(encoding="utf-8").splitlines()\n            if ln.strip() and not ln.strip().startswith("#")',
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
        "                if not plan_accepted:",
        "                if False:",
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
    # --- batch-1 hardening --------------------------------------------------
    (
        "ci: coverage back to 'any accepted chain anywhere'",
        "sdlc_ci_gate.py", "test_hardening.py",
        "uncovered = [c for c in source_changed if not plan_covers(plan, c)]",
        "uncovered = []",
    ),
    (
        "ci: active slug need not have an accepted chain",
        "sdlc_ci_gate.py", "test_hardening.py",
        "elif active_slug not in plan_accepted:",
        "elif False:",
    ),
    (
        "ci: newer artifact schema silently accepted",
        "sdlc_ci_gate.py", "test_hardening.py",
        "if repo_schema > SUPPORTED_SCHEMA:",
        "if False:",
    ),
    (
        "ci: unparsable schema version ignored",
        "sdlc_ci_gate.py", "test_hardening.py",
        "        except ValueError:",
        "        except ValueError:\n            repo_schema = SUPPORTED_SCHEMA\n        except SystemError:",
    ),
    (
        "ci: author may approve their own artifact",
        "sdlc_ci_gate.py", "test_hardening.py",
        "if author.casefold().strip() == approver.casefold().strip():",
        "if False:",
    ),
    (
        "ci: a missing approver is tolerated",
        "sdlc_ci_gate.py", "test_hardening.py",
        "if not approver:",
        "if False:",
    ),
    (
        "ci: slug traversal not validated",
        "sdlc_ci_gate.py", "test_hardening.py",
        "            bad = slug_problem(active_slug)",
        "            bad = None",
    ),
    (
        "hook: slug traversal not validated",
        "sdlc_pretooluse_hook.py", "test_hardening.py",
        'if not re.match(r"^[A-Za-z0-9][A-Za-z0-9._-]*$", slug) or slug in (".", ".."):',
        "if False:",
    ),
    (
        "gate: empty status treated as a real status",
        "sdlc_gate.py", "test_gate.py",
        'if not raw:\n        return "<empty-status>"',
        'if False:\n        return "<empty-status>"',
    ),
    # --- make_sbom.py -------------------------------------------------------
    (
        "sbom: __pycache__ not excluded (inventories build junk as policy files)",
        "make_sbom.py", "test_supply_chain.py",
        "if any(part in SKIP_DIRS for part in p.parts):\n            continue",
        "if False:\n            continue",
    ),
    (
        "sbom: hashes with MD5 while still declaring SHA-256",
        "make_sbom.py", "test_supply_chain.py",
        "h = hashlib.sha256()",
        "h = hashlib.md5()",
    ),
    (
        "sbom: emits an empty SBOM instead of refusing empty input",
        "make_sbom.py", "test_supply_chain.py",
        'raise SystemExit(f"make_sbom: no candidate files under {root}")',
        "pass",
    ),
    (
        "sbom: unsorted traversal (SBOM order varies between builds)",
        "make_sbom.py", "test_supply_chain.py",
        "for p in sorted(root.rglob(\"*\")):",
        "for p in sorted(root.rglob(\"*\"), key=lambda _: __import__('random').random()):",
    ),
    # --- build_review_prompt.py --------------------------------------------
    (
        # The explicit INVISIBLE set and the Cc/Cf category check OVERLAP on current
        # Unicode, so disabling either one alone is an equivalent mutant -- the other still
        # strips the characters. To test that sanitisation happens at all, this mutation
        # makes sanitize() a no-op, removing both guards at once.
        "review: sanitize() is a no-op (invisible injection reaches the model)",
        "build_review_prompt.py", "test_supply_chain.py",
        '    out = []\n    for ch in text:',
        '    return text\n    out = []\n    for ch in text:',
    ),
    (
        "review: explicit invisible-codepoint set emptied (loses Unicode-drift cover)",
        "build_review_prompt.py", "test_supply_chain.py",
        "INVISIBLE = {\n    0x00AD,",
        "INVISIBLE = set()\n_UNUSED_INVISIBLE = {\n    0x00AD,",
    ),
    (
        "review: fixed delimiter the attacker can guess and close",
        "build_review_prompt.py", "test_supply_chain.py",
        'token = f"{label}-{secrets.token_hex(8)}"',
        'token = f"{label}-FIXED"',
    ),
    (
        "review: oversize diff not truncated (trailing instructions pushed out)",
        "build_review_prompt.py", "test_supply_chain.py",
        "if len(raw.encode()) > cap:",
        "if False:",
    ),
    (
        "review: empty diff accepted (reviews nothing, reports success)",
        "build_review_prompt.py", "test_supply_chain.py",
        "if not diff.strip():",
        "if False:",
    ),
    # --- scale / monorepo / concurrency -------------------------------------
    (
        "ci: multi-intent .sdlc/active silently truncated to the first line",
        "sdlc_ci_gate.py", "test_scale.py",
        "if len(declared) > 1:",
        "if False:",
    ),
    (
        "ci: uncovered file no longer points at the intent that owns it",
        "sdlc_ci_gate.py", "test_scale.py",
        "if c not in owned_elsewhere and plan_covers(other_plan, c):",
        "if False:",
    ),
    (
        "ci: pointer handover not flagged as a concurrency hazard",
        "sdlc_ci_gate.py", "test_scale.py",
        'if any(c.replace("\\\\", "/") == ".sdlc/active" for c in changed):',
        "if False:",
    ),
    (
        "hook: multi-intent .sdlc/active allowed (drifts from the CI gate)",
        "sdlc_pretooluse_hook.py", "test_scale.py",
        "if len(slug_lines) > 1:",
        "if False:",
    ),
    # --- polyglot / v2 enforcement -----------------------------------------
    (
        "ci: promoted language silently drops out of the enforced suffix set",
        "sdlc_ci_gate.py", "test_polyglot.py",
        '    ".c", ".cc", ".cpp", ".cxx",',
        '    ".zzz1", ".zzz2", ".zzz3", ".zzz4",',
    ),
    (
        "ci: executable claims v1 semantics under the sdlc-gate-v2 release",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        "GATE_VERSION = 2",
        "GATE_VERSION = 1",
    ),
    (
        "ci: a source suffix remains in a pending bucket after v2 enforcement",
        "sdlc_ci_gate.py", "test_polyglot.py",
        "PENDING_SOURCE_SUFFIXES = ()",
        'PENDING_SOURCE_SUFFIXES = (".cpp",)',
    ),
    # --- fork-PR safety ------------------------------------------------------
    # These target SHIPPED DATA (the workflow template) rather than a script, which is why
    # the harness above mirrors templates/ into the work tree.
    (
        "template: advisory review job can fail the build again",
        "templates/github-workflows/sdlc-gate.yml", "test_fork_safety.py",
        "    continue-on-error: true",
        "    # continue-on-error deliberately removed by mutation",
    ),
    (
        "template: createComment unguarded (a read-only fork token would fail the job)",
        "templates/github-workflows/sdlc-gate.yml", "test_fork_safety.py",
        "            } catch (e) {",
        "            } if (false) { // catch removed by mutation",
    ),
    (
        "compat: fork read-only/no-secrets limitation undocumented",
        "COMPATIBILITY.md", "test_fork_safety.py",
        "receives **no secrets** and a **read-only** workflow token",
        "receives a workflow token",
    ),
    # --- unbound approval: a merged signed chain must stop authorising work ----
    # Anchors chosen to survive a black run. A mutation whose anchor gets reformatted
    # goes SKIPPED -- a silently disabled test, which happened before and is worse
    # than a surviving mutation because the count still looks healthy.
    (
        "ci gate: terminal chains not tracked (a shipped intent stays live)",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        "plan_shipped.add(slug)",
        "pass  # tracking removed by mutation",
    ),
    (
        "ci gate: spent chain gets the unfinished-chain message (invites re-accepting)",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        "elif active_slug in plan_shipped:",
        "elif False:",
    ),
    (
        "ci gate: SHIPPED spelled differently from the other copies",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        'SHIPPED = "shipped"',
        'SHIPPED = "merged"',
    ),
    (
        "local gate: terminal refusal falls back to accept-the-artifact advice",
        "sdlc_gate.py", "test_unbound_approval.py",
        "if terminal:",
        "if False:",
    ),
    (
        "hook: contradicting advice appended to a terminal refusal",
        "sdlc_pretooluse_hook.py", "test_unbound_approval.py",
        "if SHIPPED in detail.casefold()",
        "if False",
    ),
    # --- Accepted-for: the approval must be bound to the base it was granted for --
    (
        "ci gate: an approval bound to a DIFFERENT base is accepted anyway",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        "elif bound_to.casefold() != args.base_sha.casefold():",
        "elif False:",
    ),
    (
        "ci gate: missing binding is silently substituted with the current base",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        "if not bound_to:\n                        problems.append(",
        "if not bound_to:\n                        bound_to = args.base_sha\n                    if False:\n                        problems.append(",
    ),
    (
        "ci gate: missing --base-sha fails for the wrong reason instead of naming unverifiable binding",
        "sdlc_ci_gate.py", "test_unbound_approval.py",
        "elif not args.base_sha:",
        "elif False:",
    ),
    (
        "workflow: binding never verified because no base is passed",
        "templates/github-workflows/sdlc-gate.yml", "test_unbound_approval.py",
        "--base-sha",
        "--no-base-sha-removed-by-mutation",
    ),
    (
        "compat: Accepted-for v2 enforcement record deleted",
        "COMPATIBILITY.md", "test_unbound_approval.py",
        "`Accepted-for:` is required",
        "binding history removed by mutation",
    ),
    (
        "plan template: Accepted-for field undocumented, so nobody records it",
        "templates/plan.md", "test_unbound_approval.py",
        "- **Accepted-for:**",
        "- **Bound-to:**",
    ),
    # --- required checks must be able to REPORT ---------------------------------
    # Both filters below caused a real permanent block. These mutations put each one
    # back, so the guard is proven able to catch a reintroduction rather than merely
    # asserted to.
    (
        "shipped template: branches filter returns, deadlocking consumers' stacked PRs",
        "templates/github-workflows/sdlc-gate.yml", "test_required_checks.py",
        "  pull_request:\n",
        "  pull_request:\n    branches: [main, master]\n",
    ),
    (
        "repo CI: branches filter returns on the required `validate` check",
        ".github/workflows/validate-skills.yml", "test_required_checks.py",
        "  pull_request:\n",
        "  pull_request:\n    branches: [main]\n",
    ),
    (
        "repo CI: the warning explaining the unfiltered trigger is deleted",
        ".github/workflows/sdlc-gate-tests.yml", "test_required_checks.py",
        "DO NOT add a paths filter here",
        "Note about filters removed by mutation",
    ),
    (
        "release: test gate regresses to a stale hand-copied suite subset",
        ".github/workflows/release-attest.yml", "test_supply_chain.py",
        "for t in test_*.py; do",
        "for t in test_gate.py test_ci_gate.py; do",
    ),
    (
        "release: packages the test-mutated checkout instead of tracked bytes",
        ".github/workflows/release-attest.yml", "test_supply_chain.py",
        "git archive --format=tar",
        "tar --format=tar",
    ),
    (
        "release: SBOM inventories the larger checkout instead of the staged artifact",
        ".github/workflows/release-attest.yml", "test_supply_chain.py",
        '--root "$STAGE_DIR"',
        '--root "$SKILL_DIR"',
    ),
    (
        "release: artifact/SBOM inventory mismatch is no longer fatal",
        ".github/workflows/release-attest.yml", "test_supply_chain.py",
        'diff -u "$ARTIFACT_FILES" "$SBOM_FILES"',
        'true # inventory comparison removed by mutation',
    ),
]


def main() -> int:
    killed, survived, broken = 0, [], []

    for label, impl, suite, find, repl in MUTATIONS:
        # Some suites assert against SHIPPED DATA (a workflow template, COMPATIBILITY.md)
        # rather than against a script. Those paths are relative to the SKILL root, not to
        # scripts/. Without this the mutation would be reported BROKEN, and -- worse -- the
        # suite would fail because the file was simply absent from the work tree, which is a
        # FALSE KILL: green-to-red for the wrong reason proves nothing.
        # Where does `impl` live? Three cases, and getting this wrong shows up as
        # BROKEN (anchor/source not found) rather than as a wrong result:
        #   .github/...      -> the REPOSITORY's CI config, above the skill
        #   templates/ etc.  -> shipped data inside the skill
        #   bare name        -> a script next to this harness
        repo_relative = impl.startswith(".github/")
        skill_relative = impl.startswith(("templates/", "references/")) or "/" not in impl and impl.endswith(".md")
        if repo_relative:
            src_impl = pathlib.Path("/nonexistent")
            for parent in [SKILL, *SKILL.parents]:
                if (parent / impl).is_file():
                    src_impl = parent / impl
                    break
        else:
            src_impl = (SKILL / impl) if skill_relative else (HERE / impl)
        src_suite = HERE / suite
        if not src_impl.is_file() or not src_suite.is_file():
            broken.append(f"{label}: missing {impl} or {suite}")
            continue

        with tempfile.TemporaryDirectory() as t:
            root = pathlib.Path(t) / "skill"
            work = root / "scripts"
            work.mkdir(parents=True)
            # Copy every script so imports and sibling lookups still resolve.
            for f in HERE.glob("*.py"):
                shutil.copy2(f, work / f.name)
            # Mirror the shipped data a suite may assert against, so the suite under
            # mutation reads the MUTATED copy and not the real repository file.
            for sub in ("templates", "references"):
                if (SKILL / sub).is_dir():
                    shutil.copytree(SKILL / sub, root / sub, dirs_exist_ok=True)
            for doc in SKILL.glob("*.md"):
                shutil.copy2(doc, root / doc.name)
            # Mirror the REPOSITORY's workflows too, at the sandbox root, so a suite
            # that cross-checks real CI config reads the mutated copy instead of
            # self-skipping. Without this, assertions about this repo's own required
            # checks were unprovable: the suites walk up for .github/workflows, found
            # none in the sandbox, and reported "skip" -- so a mutation to a workflow
            # could never be killed and the harness would have called that a pass.
            # Guarded on existence, because the skill is also used standalone.
            for parent in [SKILL, *SKILL.parents]:
                if (parent / ".github" / "workflows").is_dir():
                    shutil.copytree(
                        parent / ".github" / "workflows",
                        root / ".github" / "workflows",
                        dirs_exist_ok=True,
                    )
                    break

            target = (root / impl) if (skill_relative or repo_relative) else (work / impl)
            text = target.read_text(encoding="utf-8")
            if find not in text:
                broken.append(f"{label}: anchor not found in {impl} (mutation is stale)")
                continue
            target.write_text(text.replace(find, repl, 1), encoding="utf-8")

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
