#!/usr/bin/env python3
"""sdlc_ci_gate.py — CI backstop for the AI-Native SDLC artifact chain.

Where the PreToolUse hook guards ONE session at write time, this guards the MERGE:
it does not care who produced the change, in which session, or whether a hook was
installed. It reads the repo as checked out and fails the build when the chain is
incomplete.

Deliberately the opposite failure posture from the hook:
  - the hook FAILS OPEN  (a buggy gate must not stop you editing files)
  - this   FAILS CLOSED  (anything it cannot verify is a red check)

Usage:
    sdlc_ci_gate.py [--repo .] [--changed-files-from <file>] [--require-active]

Exit 0 = chain valid, exit 1 = violation (prints a report).

What it checks
  1. Every intent/<slug>/ has intent.md, and any spec.md/plan.md present carry a
     recognised **Status:** line.
  2. Status ladder is not skipped: a signed-off spec requires an accepted intent;
     an accepted plan requires a signed-off spec.
  3. No artifact is left as the unfilled template placeholder
     ("draft | accepted | rejected").
  4. If a changed-files list is supplied, any change touching a source file must be
     covered by an intent whose plan.md is accepted.
  5. With --require-active, .sdlc/active must exist and name a real intent dir.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

ACCEPTED = "accepted"
SIGNED_OFF = "signed-off"

# Artifact-schema version this gate understands. Bump when the artifact format
# changes incompatibly; a repo declares its own in .sdlc/version. A gate older than
# the repo must refuse loudly rather than misread the artifacts.
SUPPORTED_SCHEMA = 1

# A slug names a directory under intent/. It must not be able to escape the repo:
# `root / "intent" / ".."` resolves back to root, and `root / "intent" / "/etc"`
# discards the prefix entirely because pathlib lets an absolute part win. Both were
# real traversals. Anchor to a conservative character set instead of blacklisting.
SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def slug_problem(slug: str) -> str | None:
    """Return a reason the slug is unusable, or None when it is safe."""
    if not slug:
        return "the slug is empty"
    if not SLUG_RE.match(slug):
        return (
            f"the slug {slug!r} is not a plain directory name "
            "(letters, digits, dot, underscore, hyphen; must not start with a separator "
            "or contain '/', '\\' or '..')"
        )
    if slug in (".", ".."):
        return f"the slug {slug!r} is a directory traversal"
    return None

SOURCE_SUFFIXES = (
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
    ".html", ".css", ".sh", ".sql",
)
# Paths that are process/meta, not the product; they never need plan coverage.
META_DIRS = (".sdlc", "intent", "evals", ".github", "docs")
META_FILES = ("REVIEW.md", "bands.yaml", "CLAUDE.md", "README.md")


def status_of(path: pathlib.Path) -> str:
    if not path.is_file():
        return "<missing>"
    # [ \t]* not \s* around the value: \s matches newlines, so with an EMPTY value
    # the pattern would consume the line break and capture the NEXT line's text.
    # That is a real bug this exact form prevents.
    m = re.search(
        r"(?im)^[ \t]*[-*]?[ \t]*\*\*Status:\*\*[ \t]*(.*?)[ \t]*$",
        path.read_text(encoding="utf-8", errors="replace"),
    )
    if not m:
        return "<no-status>"
    raw = m.group(1).strip()
    if not raw:
        return "<empty-status>"
    if "|" in raw:
        return "<unset-template>"
    return raw.casefold()


def satisfies(status: str, needed: str) -> bool:
    """Whole-token, case-insensitive status match.

    DUPLICATED DELIBERATELY from scripts/sdlc_gate.py. This file is vendored into
    each repo as .sdlc/scripts/sdlc_ci_gate.py and must run standalone in CI with
    no imports, so it cannot share the helper. The two copies MUST agree, and
    test_ci_gate.py asserts they do on a shared table of statuses — a divergence
    means a repo passes one gate and fails the other.

    Whole tokens, not substrings: "not-accepted" must not satisfy "accepted".
    Split on whitespace only, so the hyphenated "signed-off" stays one token.
    """
    return needed.casefold() in status.casefold().split()


def field_of(path: pathlib.Path, name: str) -> str:
    """Read a '- **Name:** value' line from an artifact. '' when absent."""
    if not path.is_file():
        return ""
    m = re.search(
        rf"(?im)^[ \t]*[-*]?[ \t]*\*\*{re.escape(name)}:\*\*[ \t]*(.*?)[ \t]*$",
        path.read_text(encoding="utf-8", errors="replace"),
    )
    return m.group(1).strip() if m else ""


def duties_problem(path: pathlib.Path, artifact: str) -> str | None:
    """Separation of duties: whoever wrote an artifact must not be its approver.

    This raises the control from an honour-system sentence in the docs to an
    explicit ATTESTED CLAIM that is committed and therefore blameable. It is not
    cryptographic proof — someone can type two names — but the claim is now
    recorded, reviewable and attributable, where before there was nothing at all.
    """
    author = field_of(path, "Author")
    approver = field_of(path, "Accepted-by")
    if not author:
        return f"{artifact}: has no '**Author:**' field, so approval cannot be attributed"
    if not approver:
        return f"{artifact}: is accepted but has no '**Accepted-by:**' field"
    if author.casefold().strip() == approver.casefold().strip():
        return (
            f"{artifact}: Author and Accepted-by are the same person "
            f"({author!r}) — an artifact may not be approved by its author"
        )
    return None


def plan_covers(plan: pathlib.Path, rel: str) -> bool:
    """True when the plan text names this file.

    Deliberately a substring test against the plan body rather than a strict
    parse: a plan legitimately writes a path inside prose, a bullet, or a code
    span, and a brittle parser would reject valid plans. The check being loose in
    FORM is fine; what matters is that the path appears at all, which is what the
    old rule failed to require.
    """
    if not plan.is_file():
        return False
    text = plan.read_text(encoding="utf-8", errors="replace").replace("\\", "/")
    return rel.replace("\\", "/") in text



def is_meta(rel: str) -> bool:
    p = rel.replace("\\", "/")
    if pathlib.PurePosixPath(p).name in META_FILES:
        return True
    return any(seg in META_DIRS for seg in p.split("/") if seg)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--changed-files-from", default="")
    ap.add_argument("--require-active", action="store_true")
    args = ap.parse_args()

    root = pathlib.Path(args.repo).resolve()
    problems: list[str] = []
    notes: list[str] = []

    # --- schema version -------------------------------------------------------
    # A gate OLDER than the repo must refuse rather than silently misread newer
    # artifacts. Absent file means schema 1 (every repo predating versioning).
    ver_file = root / ".sdlc" / "version"
    if ver_file.is_file():
        raw_ver = ver_file.read_text(encoding="utf-8", errors="replace").strip()
        try:
            repo_schema = int(raw_ver)
        except ValueError:
            problems.append(
                f".sdlc/version contains {raw_ver!r}, which is not an integer — "
                f"this gate understands schema {SUPPORTED_SCHEMA}"
            )
            repo_schema = None
        else:
            if repo_schema > SUPPORTED_SCHEMA:
                problems.append(
                    f".sdlc/version declares artifact schema {repo_schema} but this gate "
                    f"only understands {SUPPORTED_SCHEMA} — upgrade the vendored "
                    f".sdlc/scripts/sdlc_ci_gate.py before trusting its verdict"
                )
            elif repo_schema < SUPPORTED_SCHEMA:
                notes.append(
                    f"repo declares schema {repo_schema}, gate supports "
                    f"{SUPPORTED_SCHEMA} — older artifacts are read leniently"
                )
    if problems:
        # A schema mismatch makes every later reading untrustworthy, so stop here
        # rather than emitting findings derived from artifacts we may misparse.
        print(f"SDLC CI GATE FAILED ({len(problems)} problem(s)):")
        for p in problems:
            print(f"  - {p}")
        return 1

    intent_root = root / "intent"
    slugs = (
        sorted(p.name for p in intent_root.iterdir() if p.is_dir())
        if intent_root.is_dir()
        else []
    )

    if not slugs:
        notes.append("no intent/<slug>/ directories found — SDLC chain not in use here")

    plan_accepted: set[str] = set()

    for slug in slugs:
        d = intent_root / slug
        s_intent = status_of(d / "intent.md")
        s_spec = status_of(d / "spec.md")
        s_plan = status_of(d / "plan.md")

        if s_intent == "<missing>":
            problems.append(f"intent/{slug}/: intent.md is missing (Stage 1 artifact)")
        for name, st in (("intent.md", s_intent), ("spec.md", s_spec), ("plan.md", s_plan)):
            if st == "<unset-template>":
                problems.append(
                    f"intent/{slug}/{name}: Status is still the unfilled template "
                    f"placeholder — fill it in with a single value"
                )
            elif st == "<no-status>":
                problems.append(f"intent/{slug}/{name}: no '**Status:**' line found")

        # Ladder: cannot sign off a spec without an accepted intent.
        if satisfies(s_spec, SIGNED_OFF) and not satisfies(s_intent, ACCEPTED):
            problems.append(
                f"intent/{slug}/: spec.md is signed-off but intent.md is '{s_intent}' "
                f"(need '{ACCEPTED}') — a stage was skipped"
            )
        # Ladder: cannot accept a plan without a signed-off spec.
        if satisfies(s_plan, ACCEPTED) and not satisfies(s_spec, SIGNED_OFF):
            problems.append(
                f"intent/{slug}/: plan.md is accepted but spec.md is '{s_spec}' "
                f"(need '{SIGNED_OFF}') — a stage was skipped"
            )

        if (
            satisfies(s_plan, ACCEPTED)
            and satisfies(s_spec, SIGNED_OFF)
            and satisfies(s_intent, ACCEPTED)
        ):
            plan_accepted.add(slug)

        # Separation of duties, on each artifact that claims to be approved.
        for name, st, needed in (
            ("intent.md", s_intent, ACCEPTED),
            ("spec.md", s_spec, SIGNED_OFF),
            ("plan.md", s_plan, ACCEPTED),
        ):
            if satisfies(st, needed):
                bad = duties_problem(d / name, f"intent/{slug}/{name}")
                if bad:
                    problems.append(bad)

    # --- resolve the active slug (used by --require-active AND by coverage) -----
    active_slug = ""
    active_file = root / ".sdlc" / "active"
    if active_file.is_file():
        raw_lines = active_file.read_text(encoding="utf-8", errors="replace").splitlines()
        # Blank lines and # comments are ignored; anything else counts as a declaration.
        declared = [
            ln.strip() for ln in raw_lines
            if ln.strip() and not ln.strip().startswith("#")
        ]
        if len(declared) > 1:
            # Previously this read lines[0] and SILENTLY discarded the rest, so a monorepo
            # user who listed two intents got one of them quietly ignored -- the change was
            # attributed to an intent the author did not choose, with no diagnostic.
            #
            # One active intent per change is the model, deliberately: the coverage rule
            # asks "does THIS intent's plan describe THIS change", and that question has no
            # answer if several intents are active at once. A PR spanning two intents should
            # be split, which is also what makes it reviewable.
            problems.append(
                ".sdlc/active declares "
                + str(len(declared))
                + " intents ("
                + ", ".join(declared[:5])
                + ") but exactly one is allowed — a change must be attributable to a single "
                "intent. Split the change into one pull request per intent."
            )
        elif declared:
            active_slug = declared[0]
        if active_slug:
            bad = slug_problem(active_slug)
            if bad:
                problems.append(f".sdlc/active: {bad}")
                active_slug = ""  # refuse to use it for anything downstream
            elif not (root / "intent" / active_slug).is_dir():
                problems.append(
                    f".sdlc/active names '{active_slug}' but intent/{active_slug}/ does not exist"
                )

    if args.require_active:
        if not active_file.is_file():
            problems.append(".sdlc/active is missing but --require-active was set")
        elif not active_slug:
            problems.append(".sdlc/active is empty or unusable")


    # Source-file coverage.
    if args.changed_files_from:
        listing = pathlib.Path(args.changed_files_from)
        if not listing.is_file():
            problems.append(f"changed-files list not found: {listing}")
        else:
            changed = [
                ln.strip()
                for ln in listing.read_text(encoding="utf-8").splitlines()
                if ln.strip()
            ]
            source_changed = [
                c for c in changed if c.endswith(SOURCE_SUFFIXES) and not is_meta(c)
            ]
            # A PR that rewrites .sdlc/active is performing a POINTER HANDOVER, and that is
            # the one operation that can lose another intent's attribution: the pointer is a
            # single mutable file, so a branch cut before someone else's merge still carries
            # the old value and overwrites theirs on merge. Nothing here can prevent that --
            # each PR is individually valid and the fix is branch protection's "require
            # branches to be up to date" (strict=true). What the gate can do is make the
            # hazard visible at review time rather than leaving it as folklore.
            if any(c.replace("\\", "/") == ".sdlc/active" for c in changed):
                notes.append(
                    "this change rewrites .sdlc/active — concurrency hazard: the active "
                    "pointer is a single shared value, so a branch cut before another "
                    "intent's merge will overwrite it and silently drop that attribution. "
                    "Require branches to be up to date (strict status checks) if several "
                    "intents are in flight at once."
                )
            if not source_changed:
                notes.append("no product source files changed")
            elif not (root / ".sdlc").is_dir():
                # Repo has not opted in to the .sdlc/active convention. Fall back to
                # the coarse rule and SAY SO, rather than pretending it is precise.
                if not plan_accepted:
                    problems.append(
                        "source files changed but NO intent has a fully accepted chain "
                        "(intent accepted + spec signed-off + plan accepted):\n    "
                        + "\n    ".join(source_changed[:20])
                    )
                else:
                    notes.append(
                        f"{len(source_changed)} source file(s) changed; coarse check only "
                        f"(no .sdlc/ directory) against accepted chain(s): "
                        f"{', '.join(sorted(plan_accepted))}"
                    )
            elif not active_slug:
                problems.append(
                    "source files changed and this repo uses .sdlc/, but no usable active "
                    "slug is declared in .sdlc/active — the change is not attributable to "
                    "any intent"
                )
            elif active_slug not in plan_accepted:
                problems.append(
                    f"source files changed but the active intent '{active_slug}' does not "
                    f"have a fully accepted chain (intent accepted + spec signed-off + "
                    f"plan accepted)"
                )
            else:
                # The precise rule: the ACTIVE plan must actually name each file.
                # The old rule only asked whether SOME accepted chain existed anywhere,
                # so one historical acceptance permanently satisfied it.
                plan = root / "intent" / active_slug / "plan.md"
                uncovered = [c for c in source_changed if not plan_covers(plan, c)]
                if uncovered:
                    # In a monorepo the useful question is not merely "is this file in the
                    # active plan" but "which intent DOES own it". Without that, the message
                    # sends the reader to edit the active plan, which is usually the wrong
                    # fix -- the right fix is normally to split the pull request.
                    owned_elsewhere: dict[str, str] = {}
                    intent_root = root / "intent"
                    if intent_root.is_dir():
                        for other in sorted(p.name for p in intent_root.iterdir() if p.is_dir()):
                            if other == active_slug:
                                continue
                            other_plan = intent_root / other / "plan.md"
                            if not other_plan.is_file():
                                continue
                            for c in uncovered:
                                if c not in owned_elsewhere and plan_covers(other_plan, c):
                                    owned_elsewhere[c] = other

                    msg = (
                        f"these changed source files are not named in "
                        f"intent/{active_slug}/plan.md, so the plan does not describe the "
                        f"change being made:\n    " + "\n    ".join(uncovered[:20])
                    )
                    if owned_elsewhere:
                        others = sorted(set(owned_elsewhere.values()))
                        msg += (
                            "\n\n  These files ARE named by another intent's plan, so this "
                            "looks like a pull request spanning several intents:\n    "
                            + "\n    ".join(
                                f"{c} -> intent/{owned_elsewhere[c]}/plan.md"
                                for c in sorted(owned_elsewhere)[:20]
                            )
                            + f"\n\n  Split this into one pull request per intent "
                            f"({', '.join([active_slug] + others)}), rather than widening "
                            f"intent/{active_slug}/plan.md to cover work it does not describe."
                        )
                    problems.append(msg)
                else:
                    notes.append(
                        f"{len(source_changed)} source file(s) changed, all named in "
                        f"intent/{active_slug}/plan.md"
                    )


    for n in notes:
        print(f"note: {n}")

    if problems:
        print()
        print(f"SDLC CI GATE FAILED ({len(problems)} problem(s)):")
        for p in problems:
            print(f"  - {p}")
        print()
        print("The artifact chain must be intent.md (accepted) -> spec.md (signed-off)")
        print("-> plan.md (accepted) before product source code is merged.")
        return 1

    print("SDLC CI GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
