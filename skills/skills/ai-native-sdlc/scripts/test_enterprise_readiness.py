"""test_enterprise_readiness.py — enterprise positioning must stay literally true.

WHY THIS EXISTS: the recurring defect in this project is not broken code, it is documents
claiming more than reality. The enterprise story is the highest-risk instance of that,
because the failure mode is silent: a reader adopts this as a compliance control on the
strength of prose, and nothing goes red.

So the claims are treated as data. This suite asserts that:

  * all four adoption positions are stated, and the two that are NOT achieved still say so;
  * the readiness score, its denominator and the standalone ceiling stay together;
  * the three enterprise-owned controls each carry an ownership boundary, an acceptance
    contract, evidence, verification, bypass modes and an explicit statement that this
    skill does not provide them;
  * the roadmap names exactly the six agreed follow-up slugs, each still `proposed`;
  * longitudinal evidence cannot be closed by running a test; and
  * the mutation evidence count matches what the harness actually contains.

The last point is the reason the count is DERIVED rather than written here. A hard-coded
number in a test is the same defect as a hard-coded number in prose: it goes stale the day
the harness grows. `mutation_proof.py` is the single source of truth for how much mutation
evidence exists, and the documents must agree with it.

Claiming LESS than reality is fine. Claiming MORE is a build failure.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent

SKILL_MD = SKILL / "SKILL.md"
ADOPTION = SKILL / "references" / "enterprise-adoption.md"
ROADMAP = SKILL / "references" / "enterprise-roadmap.md"
LIMITATIONS = SKILL / "references" / "limitations.md"
COMPAT = SKILL / "COMPATIBILITY.md"
HARNESS = HERE / "mutation_proof.py"

FAILURES: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        print(f"  ok   {name}")
    else:
        print(f"  FAIL {name} {detail}")
        FAILURES.append(name)


def read(path: pathlib.Path) -> str:
    """Missing file is a FAILURE, not a crash: absence is the thing being tested."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        FAILURES.append(f"unreadable: {path.name} ({exc})")
        return ""


def sections(text: str, level: str) -> dict[str, str]:
    """Split markdown into {heading: body} at one heading level."""
    out: dict[str, str] = {}
    pattern = re.compile(rf"^{re.escape(level)} (.+)$", re.MULTILINE)
    marks = list(pattern.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(1).strip()] = text[m.start():end]
    return out


def line_with(text: str, needle: str) -> str | None:
    for line in text.splitlines():
        if needle.casefold() in line.casefold():
            return line
    return None


def mutation_total() -> int | None:
    """Count MUTATIONS entries by parsing the harness — never by trusting a written number."""
    src = read(HARNESS)
    if not src:
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        FAILURES.append(f"mutation_proof.py does not parse: {exc}")
        return None
    for node in ast.walk(tree):
        # The harness declares `MUTATIONS: list[tuple[...]] = [...]`, so the annotated form
        # is the one that actually occurs; accept the plain form too rather than depending
        # on that detail staying put.
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = list(node.targets), node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = [node.target], node.value
        for target in targets:
            if isinstance(target, ast.Name) and target.id == "MUTATIONS":
                if isinstance(value, (ast.List, ast.Tuple)):
                    return len(value.elts)
    FAILURES.append("mutation_proof.py has no MUTATIONS list to count")
    return None


# --- 1. adoption tiers -------------------------------------------------------------
# Each tier's status must sit ON THE SAME LINE as the tier name. Presence of the words
# somewhere in the file is not evidence: the failure being prevented is a tier quietly
# promoted while the vocabulary stays intact.
TIERS = [
    ("Individual or small team", "usable now"),
    ("Controlled enterprise pilot", "conditional"),
    ("Enterprise-wide mandatory control", "not achieved"),
    ("Regulated or auditable compliance control", "not achieved"),
]

# --- 2. external control contracts ------------------------------------------------
CONTROL_SUBSECTIONS = [
    "Owner and boundary",
    "Minimum required properties",
    "Acceptance contract",
    "Reference architecture (non-normative)",
    "Evidence package",
    "Verification and negative controls",
    "Failure and bypass modes",
    "What this skill does not provide",
]

CONTROL_COMMON = ["enterprise-owned", "not provided by this skill", "non-normative"]

CONTROLS = {
    "Organisation policy plane": [
        "centrally managed",
        "cannot weaken",
        "exception",
        "verified identity",
        "always report",
        "fleet",
    ],
    "External tamper-evident audit sink": [
        "outside",
        "append-only",
        "worm",
        "integrity",
        "retention",
        "retrieval",
        "denied",
    ],
    "Independent assurance": [
        "independence",
        "commit under review",
        "threat model",
        "adversarial",
        "severity",
        "reassessment",
        "self-authored tests are not independence",
    ],
}

# --- 3. roadmap -------------------------------------------------------------------
REQUIRED_SLUGS = {
    "operational-ownership",
    "enterprise-telemetry",
    "schema-migration-fleet-inventory",
    "stage6-feedback-loop",
    "production-scale-evidence",
    "longitudinal-operational-evidence",
}

WORKSTREAM_FIELDS = [
    "- **Problem:**",
    "- **Enterprise value:**",
    "- **Depends on:**",
    "- **Bounded deliverable:**",
    "- **Verification target:**",
    "- **Exit evidence:**",
    "- **Non-goals:**",
    "- **Follow-up intent slug:**",
    "- **Status:** proposed",
]


def main() -> int:
    skill = read(SKILL_MD)
    adoption = read(ADOPTION)
    roadmap = read(ROADMAP)
    limits = read(LIMITATIONS)
    compat = read(COMPAT)

    print("adoption positioning (SKILL.md)")
    for tier, status in TIERS:
        row = line_with(skill, tier)
        check(f"tier stated: {tier}", row is not None)
        if row is not None:
            check(
                f"tier status is '{status}': {tier}",
                status.casefold() in row.casefold(),
                f"-> {row.strip()[:110]}",
            )

    print("score and ceiling")
    for token in ("36/80", "45%", "48%"):
        check(f"SKILL.md states {token}", token in skill)
    ceiling_line = line_with(skill, "48%")
    check(
        "48% is identified as the standalone ceiling",
        ceiling_line is not None
        and any(w in ceiling_line.casefold() for w in ("ceiling", "self-contained", "standalone")),
    )
    # Any OTHER denominator-80 score is a silent promotion.
    others = {m for m in re.findall(r"\b(\d{1,2})/80\b", skill + limits) if m != "36"}
    check("no competing /80 readiness score", not others, f"found {sorted(others)}")
    check(
        "documentation is stated not to raise the score",
        "do not raise" in skill.casefold() or "does not raise" in skill.casefold(),
    )

    print("navigation")
    for ref in ("references/enterprise-adoption.md", "references/enterprise-roadmap.md"):
        check(f"SKILL.md links {ref}", ref in skill)
        check(f"limitations.md links {ref}", ref in limits)

    print("external control contracts (enterprise-adoption.md)")
    control_sections = sections(adoption, "##")
    for control, tokens in CONTROLS.items():
        match = None
        for heading, body in control_sections.items():
            if control.casefold() in heading.casefold():
                match = body
                break
        check(f"control section present: {control}", match is not None)
        if match is None:
            continue
        low = match.casefold()
        for sub in CONTROL_SUBSECTIONS:
            check(f"{control}: has '{sub}'", sub.casefold() in low)
        for token in CONTROL_COMMON + tokens:
            check(f"{control}: states '{token}'", token.casefold() in low)

    check(
        "adoption doc keeps examples vendor-neutral",
        "equivalent controls" in adoption.casefold(),
    )
    check(
        "adoption doc denies that copying an example proves compliance",
        "does not prove" in adoption.casefold() or "is not proof" in adoption.casefold(),
    )

    print("roadmap (enterprise-roadmap.md)")
    found_slugs = set(re.findall(r"\*\*Follow-up intent slug:\*\*\s*`([a-z0-9-]+)`", roadmap))
    check(
        "roadmap names exactly the six agreed slugs",
        found_slugs == REQUIRED_SLUGS,
        f"missing={sorted(REQUIRED_SLUGS - found_slugs)} extra={sorted(found_slugs - REQUIRED_SLUGS)}",
    )
    workstreams = sections(roadmap, "###")
    ws_bodies = [b for h, b in workstreams.items() if "Workstream" in h]
    check("six workstream sections", len(ws_bodies) == 6, f"found {len(ws_bodies)}")
    for body in ws_bodies:
        title = body.splitlines()[0].strip("# ").strip()
        for field in WORKSTREAM_FIELDS:
            check(f"{title[:46]}: has '{field}'", field.casefold() in body.casefold())

    for phase in ("Phase 0", "Phase 1", "Phase 2", "Phase 3"):
        check(f"roadmap defines {phase}", phase in roadmap)
    low_roadmap = roadmap.casefold()
    check("roadmap is not an SLA", "not an sla" in low_roadmap)
    check("roadmap claims no funding", "no funded" in low_roadmap or "unfunded" in low_roadmap)
    check(
        "roadmap requires a new accepted intent per workstream",
        "accepted intent" in low_roadmap,
    )

    longitudinal = None
    for heading, body in workstreams.items():
        if "longitudinal" in (heading + body).casefold() and "Workstream" in heading:
            longitudinal = body
    check("longitudinal workstream section found", longitudinal is not None)
    if longitudinal is not None:
        low = longitudinal.casefold()
        check("longitudinal evidence needs elapsed real time", "elapsed" in low)
        check(
            "longitudinal evidence cannot be closed synthetically",
            "synthetic" in low and ("cannot" in low or "not be closed" in low),
        )

    print("evidence freshness")
    total = mutation_total()
    check("mutation harness count is derivable", total is not None)
    if total is not None:
        check(
            f"SKILL.md reports the actual mutation count ({total})",
            str(total) in skill,
        )
        check(
            f"limitations.md reports the actual mutation count ({total})",
            str(total) in limits,
        )
    for doc, text in (("SKILL.md", skill), ("limitations.md", limits)):
        check(f"{doc} drops the stale 27-mutation claim", "27 mutation" not in text.casefold())

    polyglot = line_with(compat, "Polyglot repos")
    check("COMPATIBILITY.md has a polyglot row", polyglot is not None)
    if polyglot is not None:
        check(
            "polyglot row no longer contradicts the shipped polyglot tests",
            "untested" not in polyglot.casefold(),
            f"-> {polyglot.strip()[:110]}",
        )
        check(
            "polyglot row says the coverage is synthetic",
            "synthetic" in polyglot.casefold(),
        )
    check(
        "fork runtime semantics stay unproven",
        "runtime unproven" in compat.casefold() or "documented_untested" in compat,
    )

    print("no promotion of synthetic or self-authored evidence")
    low_limits = limits.casefold()
    check(
        "limitations.md still separates synthetic CI evidence from production adoption",
        "synthetic" in low_limits,
    )
    check(
        "limitations.md still denies independent assurance",
        "independent" in low_limits and "not addressed" in low_limits,
    )
    for phrase in (
        "independently audited",
        "compliance is proven",
        "enterprise-ready today",
        "production-scale evidence exists",
    ):
        for doc, text in (
            ("SKILL.md", skill),
            ("enterprise-adoption.md", adoption),
            ("enterprise-roadmap.md", roadmap),
            ("limitations.md", limits),
        ):
            check(f"{doc} avoids overclaim '{phrase}'", phrase.casefold() not in text.casefold())

    print()
    if FAILURES:
        print(f"FAILED ({len(FAILURES)}):")
        for f in FAILURES:
            print("  -", f)
        return 1
    print("enterprise readiness claims are consistent with reality")
    return 0


if __name__ == "__main__":
    sys.exit(main())
