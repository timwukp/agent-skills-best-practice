#!/usr/bin/env python3
"""
Credit measurement and estimation tool for AWS Kiro Skills.

Commands:
  init                          Initialize results file
  add <name> <start> <end>      Record a test result
  benchmark <scenario>          Run a benchmark scenario interactively
  estimate                      Estimate credits for a custom workload
  plan                          Estimate credits for a sprint
  summary [--period weekly]     Show summary of results
  export                        Export results to markdown
  baselines                     Show current baselines from benchmark data
"""

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

RESULTS_FILE = "credit-test-results.json"
BENCHMARK_DIR = Path(__file__).parent / "benchmark" / "scenarios"

# Complexity scoring weights
COMPLEXITY_WEIGHTS = {
    "source_lines": (50, 1),      # +1 per 50 lines
    "mocks": (1, 1),              # +1 per mock
    "branches": (3, 1),           # +1 per 3 branches
    "annotations": (3, 1),        # +1 per 3 annotations
    "nesting_levels": (1, 1),     # +1 per nesting level
    "dynamic_selectors": (1, 2),  # +2 per dynamic selector
}

# Default baselines (used when no benchmark data exists)
DEFAULT_BASELINES = {
    "java-unit": {"per_test": 0.065, "note": "default estimate, run benchmarks for accuracy"},
    "api": {"per_test": 0.077, "note": "default estimate, run benchmarks for accuracy"},
    "ui": {"per_test": 0.210, "note": "default estimate, run benchmarks for accuracy"},
}

CATEGORIES = {
    "java-simple": "java-unit",
    "java-complex": "java-unit",
    "api-simple": "api",
    "api-complex": "api",
    "ui-simple": "ui",
    "ui-complex": "ui",
}

TEST_COUNTS = {
    "java-simple": 3,
    "java-complex": 3,
    "api-simple": 3,
    "api-complex": 3,
    "ui-simple": 1,
    "ui-complex": 1,
}


def init_results():
    """Initialize results file."""
    if not Path(RESULTS_FILE).exists():
        data = {
            "test_date": datetime.now().isoformat(),
            "model": "unknown",
            "kiro_version": "unknown",
            "tests": [],
            "baselines": {},
        }
        save_results(data)
        print(f"Created {RESULTS_FILE}")
        print("Update 'model' and 'kiro_version' fields with your environment info.")
    else:
        print(f"{RESULTS_FILE} already exists. Use 'add' or 'benchmark' to record data.")


def save_results(data):
    """Save results to JSON file."""
    with open(RESULTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_results():
    """Load results from JSON file."""
    if not Path(RESULTS_FILE).exists():
        print(f"No {RESULTS_FILE} found. Run 'python track_credits.py init' first.")
        sys.exit(1)
    with open(RESULTS_FILE, "r") as f:
        return json.load(f)


def compute_complexity_score(**kwargs):
    """Compute complexity score from factors."""
    score = 1  # minimum
    for key, value in kwargs.items():
        if key in COMPLEXITY_WEIGHTS and value:
            divisor, weight = COMPLEXITY_WEIGHTS[key]
            score += math.ceil(value / divisor) * weight
    return score


def get_baselines():
    """Get baselines from recorded benchmark data, falling back to defaults."""
    data = load_results()
    baselines = {}

    for category in ["java-unit", "api", "ui"]:
        # Find benchmark entries for this category (complexity_score == 1 preferred)
        cat_tests = [
            t for t in data["tests"]
            if t.get("category") == category
        ]

        # Prefer simple benchmarks (complexity_score 1) for baseline
        simple = [t for t in cat_tests if t.get("complexity_score", 0) <= 1]
        source = simple if simple else cat_tests

        if source:
            total_credits = sum(t["credits_used"] for t in source)
            total_tests = sum(t.get("test_count", 1) for t in source)
            per_test = total_credits / total_tests if total_tests > 0 else 0
            baselines[category] = {
                "per_test": round(per_test, 4),
                "sample_count": len(source),
                "note": "measured from your benchmarks",
            }
        else:
            baselines[category] = DEFAULT_BASELINES[category].copy()

    return baselines


def add_test(test_name, start_credits, end_credits, notes="",
             category=None, complexity_score=None, test_count=None, source_lines=None):
    """Record a test result."""
    data = load_results()

    used = start_credits - end_credits

    test_entry = {
        "name": test_name,
        "start_credits": start_credits,
        "end_credits": end_credits,
        "credits_used": round(used, 4),
        "timestamp": datetime.now().isoformat(),
        "notes": notes,
    }

    if category:
        test_entry["category"] = category
    else:
        # Auto-detect category from name
        name_lower = test_name.lower()
        if "ui" in name_lower or "selenium" in name_lower:
            test_entry["category"] = "ui"
        elif "api" in name_lower:
            test_entry["category"] = "api"
        elif "java" in name_lower:
            test_entry["category"] = "java-unit"

    if complexity_score is not None:
        test_entry["complexity_score"] = complexity_score
    if test_count is not None:
        test_entry["test_count"] = test_count
    if source_lines is not None:
        test_entry["source_lines"] = source_lines

    data["tests"].append(test_entry)
    save_results(data)

    print(f"\nRecorded: {test_name}")
    print(f"  Credits used: {round(used, 4)}")
    if test_count and test_count > 0:
        print(f"  Per test: {round(used / test_count, 4)}")
    print(f"  Total entries recorded: {len(data['tests'])}")


def run_benchmark(scenario_name):
    """Interactive benchmark for a specific scenario."""
    scenario_file = BENCHMARK_DIR / f"{scenario_name}.md"
    if not scenario_file.exists():
        available = [f.stem for f in BENCHMARK_DIR.glob("*.md")]
        print(f"Scenario '{scenario_name}' not found.")
        print(f"Available: {', '.join(sorted(available))}")
        sys.exit(1)

    # Parse the scenario file
    content = scenario_file.read_text()

    # Extract category, complexity score, and test count
    category = CATEGORIES.get(scenario_name, "unknown")
    test_count = TEST_COUNTS.get(scenario_name, 1)

    # Extract complexity score from file
    complexity_score = 1
    for line in content.split("\n"):
        if "Complexity score:" in line:
            try:
                complexity_score = int(line.split(":")[-1].strip())
            except ValueError:
                pass

    # Extract prompt
    prompt_lines = []
    in_prompt = False
    prompt_fence_count = 0
    for line in content.split("\n"):
        if line.strip() == "## Prompt":
            in_prompt = True
            continue
        if in_prompt:
            if line.strip() == "```" and prompt_fence_count == 0:
                prompt_fence_count = 1
                continue
            elif line.strip() == "```" and prompt_fence_count == 1:
                break
            elif prompt_fence_count == 1:
                prompt_lines.append(line)

    prompt = "\n".join(prompt_lines)

    print(f"\n{'='*60}")
    print(f"BENCHMARK: {scenario_name}")
    print(f"Category: {category} | Tests: {test_count} | Complexity: {complexity_score}")
    print(f"{'='*60}")
    print()
    print("INSTRUCTIONS:")
    print("1. Start a FRESH Kiro conversation (important for accurate measurement)")
    print("2. Check your credit balance and note it")
    print("3. Paste the following prompt into Kiro:")
    print()
    print(f"--- PROMPT START ---")
    print(prompt)
    print(f"--- PROMPT END ---")
    print()
    print("4. Wait for Kiro to finish generating")
    print("5. Check your credit balance again")
    print()

    try:
        start = float(input("Enter starting credit balance: "))
        end = float(input("Enter ending credit balance: "))
        extra_notes = input("Any notes (press Enter to skip): ").strip()
    except (ValueError, EOFError):
        print("Invalid input. Benchmark cancelled.")
        sys.exit(1)

    notes = f"Benchmark: {scenario_name}. {extra_notes}".strip()
    add_test(
        name=f"benchmark-{scenario_name}",
        start_credits=start,
        end_credits=end,
        notes=notes,
        category=category,
        complexity_score=complexity_score,
        test_count=test_count,
    )

    used = start - end
    per_test = used / test_count if test_count > 0 else used
    print(f"\n  Credits per test: {round(per_test, 4)}")
    print(f"  This becomes your baseline for '{category}' category.")


def estimate_credits(**kwargs):
    """Estimate credits based on complexity factors and baselines."""
    test_type = kwargs.get("type", "java-unit")
    tests = kwargs.get("tests", 3)
    source_lines = kwargs.get("source_lines", 0)
    mocks = kwargs.get("mocks", 0)
    branches = kwargs.get("branches", 0)
    annotations = kwargs.get("annotations", 0)
    nesting = kwargs.get("nesting_levels", 0)
    dynamic_sel = kwargs.get("dynamic_selectors", 0)

    baselines = get_baselines()
    baseline = baselines.get(test_type, DEFAULT_BASELINES.get(test_type, {"per_test": 0.1}))

    score = compute_complexity_score(
        source_lines=source_lines,
        mocks=mocks,
        branches=branches,
        annotations=annotations,
        nesting_levels=nesting,
        dynamic_selectors=dynamic_sel,
    )

    per_test = baseline["per_test"] * score
    total = per_test * tests
    # Fix iterations estimate (20% chance of 1 retry per test)
    fix_overhead = total * 0.2

    print(f"\n{'='*60}")
    print(f"CREDIT ESTIMATE")
    print(f"{'='*60}")
    print(f"  Type: {test_type}")
    print(f"  Baseline per test: {baseline['per_test']} ({baseline.get('note', '')})")
    print(f"  Complexity score: {score}")
    print(f"    Source lines: {source_lines} (+{math.ceil(source_lines/50) if source_lines else 0})")
    print(f"    Mocks/stubs: {mocks} (+{mocks})")
    print(f"    Branches: {branches} (+{math.ceil(branches/3) if branches else 0})")
    print(f"    Annotations: {annotations} (+{math.ceil(annotations/3) if annotations else 0})")
    if test_type == "ui":
        print(f"    Dynamic selectors: {dynamic_sel} (+{dynamic_sel * 2})")
    print(f"  Tests to generate: {tests}")
    print(f"{'='*60}")
    print(f"  Estimated per test: {round(per_test, 4)} credits")
    print(f"  Estimated total: {round(total, 4)} credits")
    print(f"  Fix iteration buffer (20%): {round(fix_overhead, 4)} credits")
    print(f"  TOTAL WITH BUFFER: {round(total + fix_overhead, 4)} credits")
    print(f"{'='*60}")

    return {"per_test": per_test, "total": total, "with_buffer": total + fix_overhead, "score": score}


def plan_sprint(**kwargs):
    """Estimate credits for a full sprint."""
    java_classes = kwargs.get("java_classes", 0)
    api_endpoints = kwargs.get("api_endpoints", 0)
    ui_flows = kwargs.get("ui_flows", 0)
    avg_complexity = kwargs.get("avg_complexity", "medium")
    developers = kwargs.get("developers", 1)

    complexity_multipliers = {"low": 2, "medium": 5, "high": 10}
    mult = complexity_multipliers.get(avg_complexity, 5)

    baselines = get_baselines()

    java_baseline = baselines.get("java-unit", DEFAULT_BASELINES["java-unit"])["per_test"]
    api_baseline = baselines.get("api", DEFAULT_BASELINES["api"])["per_test"]
    ui_baseline = baselines.get("ui", DEFAULT_BASELINES["ui"])["per_test"]

    # 3 tests per class/endpoint, 1 per UI flow
    java_credits = java_classes * 3 * java_baseline * mult
    api_credits = api_endpoints * 3 * api_baseline * mult
    ui_credits = ui_flows * 1 * ui_baseline * mult

    subtotal = java_credits + api_credits + ui_credits
    fix_overhead = subtotal * 0.2
    safety_margin = subtotal * 0.3
    total = subtotal + fix_overhead + safety_margin

    per_dev = total / developers if developers > 0 else total

    print(f"\n{'='*60}")
    print(f"SPRINT CREDIT PLAN")
    print(f"{'='*60}")
    print(f"  Avg complexity: {avg_complexity} (multiplier: {mult}x)")
    print(f"  Developers: {developers}")
    print()
    print(f"  Java unit tests: {java_classes} classes x 3 tests x {java_baseline}/test x {mult}x")
    print(f"    = {round(java_credits, 2)} credits")
    print(f"  API tests: {api_endpoints} endpoints x 3 tests x {api_baseline}/test x {mult}x")
    print(f"    = {round(api_credits, 2)} credits")
    print(f"  UI tests: {ui_flows} flows x 1 test x {ui_baseline}/test x {mult}x")
    print(f"    = {round(ui_credits, 2)} credits")
    print()
    print(f"  Subtotal: {round(subtotal, 2)} credits")
    print(f"  Fix iterations (20%): {round(fix_overhead, 2)} credits")
    print(f"  Safety margin (30%): {round(safety_margin, 2)} credits")
    print(f"{'='*60}")
    print(f"  TOTAL: {round(total, 2)} credits")
    print(f"  Per developer: {round(per_dev, 2)} credits")
    print(f"{'='*60}")
    print()
    print("  Note: These estimates use your measured baselines (or defaults).")
    print("  Run 'python track_credits.py baselines' to see current baselines.")
    print("  Run benchmarks to improve accuracy.")


def show_baselines():
    """Display current baselines."""
    baselines = get_baselines()
    print(f"\n{'='*60}")
    print(f"CURRENT BASELINES (per test)")
    print(f"{'='*60}")
    for cat, info in baselines.items():
        source = info.get("note", "")
        samples = info.get("sample_count", 0)
        print(f"  {cat:12s}: {info['per_test']:.4f} credits/test  ({source})")
        if samples:
            print(f"               based on {samples} benchmark(s)")
    print(f"{'='*60}")
    print("\nRun benchmarks to replace default estimates with measured data:")
    print("  python track_credits.py benchmark java-simple")
    print("  python track_credits.py benchmark api-simple")
    print("  python track_credits.py benchmark ui-simple")


def show_summary(period=None):
    """Display summary of all tests."""
    data = load_results()

    if not data["tests"]:
        print("No tests recorded yet. Run benchmarks or add test results.")
        return

    tests = data["tests"]

    # Filter by period
    if period == "weekly":
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        tests = [t for t in tests if t.get("timestamp", "") >= cutoff]
        if not tests:
            print("No tests recorded in the last 7 days.")
            return

    print(f"\n{'='*60}")
    print(f"Credit Test Results Summary")
    print(f"Model: {data.get('model', 'unknown')}")
    print(f"Kiro Version: {data.get('kiro_version', 'unknown')}")
    print(f"{'='*60}")

    # Group by category
    categories = {}
    for t in tests:
        cat = t.get("category", "unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t)

    category_labels = {
        "java-unit": ("Java Unit Tests", "10-15"),
        "api": ("REST API Tests", "15-20"),
        "ui": ("Selenium UI Tests", "30-50"),
        "unknown": ("Uncategorized", "N/A"),
    }

    for cat, cat_tests in sorted(categories.items()):
        label, claimed = category_labels.get(cat, (cat, "N/A"))
        total = sum(t["credits_used"] for t in cat_tests)
        total_test_count = sum(t.get("test_count", 1) for t in cat_tests)
        avg_per_test = total / total_test_count if total_test_count > 0 else 0

        print(f"\n  {label}")
        print(f"  {'-'*56}")
        print(f"    Entries: {len(cat_tests)}")
        print(f"    Total tests generated: {total_test_count}")
        print(f"    Total credits: {round(total, 4)}")
        print(f"    Avg credits/test: {round(avg_per_test, 4)}")
        print(f"    Original claimed range: {claimed} per test")

        for t in cat_tests:
            tc = t.get("test_count", 1)
            per = round(t["credits_used"] / tc, 4) if tc > 0 else t["credits_used"]
            score = t.get("complexity_score", "?")
            print(f"      {t['name']}: {round(t['credits_used'], 4)} credits "
                  f"({tc} tests, {per}/test, complexity={score})")
            if t.get("notes"):
                print(f"        {t['notes']}")

    print(f"\n{'='*60}")
    total_all = sum(t["credits_used"] for t in tests)
    print(f"  Total credits used: {round(total_all, 4)}")
    print(f"  Total entries: {len(tests)}")
    print(f"{'='*60}\n")


def export_markdown():
    """Export results as markdown with enhanced analysis."""
    data = load_results()

    if not data["tests"]:
        print("No tests to export.")
        return

    baselines = get_baselines()

    md = f"""# Credit Test Results

**Model:** {data.get('model', 'unknown')}
**Kiro Version:** {data.get('kiro_version', 'unknown')}
**Test Date:** {data.get('test_date', 'unknown')}
**Total Entries:** {len(data['tests'])}

## Raw Results

| Test Name | Category | Credits Used | Test Count | Per Test | Complexity | Notes |
|-----------|----------|--------------|------------|----------|------------|-------|
"""

    for t in data["tests"]:
        tc = t.get("test_count", 1)
        per = round(t["credits_used"] / tc, 4) if tc > 0 else round(t["credits_used"], 4)
        cat = t.get("category", "unknown")
        score = t.get("complexity_score", "?")
        md += (f"| {t['name']} | {cat} | {round(t['credits_used'], 4)} "
               f"| {tc} | {per} | {score} | {t.get('notes', '')} |\n")

    md += "\n## Measured Baselines\n\n"
    md += "| Category | Per Test | Source | Samples |\n"
    md += "|----------|----------|--------|---------|\n"
    for cat, info in baselines.items():
        samples = info.get("sample_count", "N/A")
        md += f"| {cat} | {info['per_test']:.4f} | {info.get('note', '')} | {samples} |\n"

    # Category summaries
    categories = {}
    for t in data["tests"]:
        cat = t.get("category", "unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(t)

    md += "\n## Category Summary\n\n"
    for cat, cat_tests in sorted(categories.items()):
        total_credits = sum(t["credits_used"] for t in cat_tests)
        total_tests = sum(t.get("test_count", 1) for t in cat_tests)
        avg = total_credits / total_tests if total_tests > 0 else 0
        md += f"- **{cat}**: {round(avg, 4)} credits/test avg "
        md += f"({len(cat_tests)} entries, {total_tests} tests)\n"

    md += "\n## How to Use These Baselines\n\n"
    md += "```\n"
    md += "# Estimate credits for a specific workload\n"
    md += "python track_credits.py estimate --type java-unit --source-lines 200 "
    md += "--mocks 3 --branches 8 --tests 3\n\n"
    md += "# Plan a sprint\n"
    md += "python track_credits.py plan --java-classes 10 --api-endpoints 5 "
    md += "--ui-flows 2 --avg-complexity medium\n"
    md += "```\n"

    output_file = "credit-test-results.md"
    with open(output_file, "w") as f:
        f.write(md)

    print(f"Exported to {output_file}")


def print_usage():
    """Print usage information."""
    print("""
Usage: python track_credits.py <command> [options]

Commands:
  init
      Initialize the results file.

  add <test_name> <start_credits> <end_credits> [notes]
      Record a test result.
      Example: python track_credits.py add "OrderService-3tests" 2000 1999.7 "3 tests with Mockito"

  benchmark <scenario>
      Run an interactive benchmark scenario.
      Scenarios: java-simple, java-complex, api-simple, api-complex, ui-simple, ui-complex
      Example: python track_credits.py benchmark java-simple

  estimate --type <type> [--source-lines N] [--mocks N] [--branches N]
           [--annotations N] [--nesting-levels N] [--dynamic-selectors N] [--tests N]
      Estimate credits for a workload based on complexity.
      Types: java-unit, api, ui
      Example: python track_credits.py estimate --type java-unit --source-lines 200 --mocks 3 --tests 3

  plan --java-classes N --api-endpoints N --ui-flows N
       [--avg-complexity low|medium|high] [--developers N]
      Estimate credits for a full sprint.
      Example: python track_credits.py plan --java-classes 10 --api-endpoints 5 --ui-flows 2

  baselines
      Show current baselines from benchmark data.

  summary [--period weekly]
      Show summary of all recorded results.

  export
      Export results to credit-test-results.md.
""")


def parse_estimate_args(args):
    """Parse --key value pairs for estimate command."""
    kwargs = {"type": "java-unit", "tests": 3}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--") and i + 1 < len(args):
            key = arg[2:].replace("-", "_")
            val = args[i + 1]
            try:
                val = int(val)
            except ValueError:
                pass
            kwargs[key] = val
            i += 2
        else:
            i += 1
    return kwargs


def parse_plan_args(args):
    """Parse --key value pairs for plan command."""
    kwargs = {
        "java_classes": 0, "api_endpoints": 0, "ui_flows": 0,
        "avg_complexity": "medium", "developers": 1,
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--") and i + 1 < len(args):
            key = arg[2:].replace("-", "_")
            val = args[i + 1]
            try:
                val = int(val)
            except ValueError:
                pass
            kwargs[key] = val
            i += 2
        else:
            i += 1
    return kwargs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "init":
        init_results()

    elif cmd == "add":
        if len(sys.argv) < 5:
            print("Usage: python track_credits.py add <test_name> <start_credits> <end_credits> [notes]")
            sys.exit(1)
        test_name = sys.argv[2]
        start = float(sys.argv[3])
        end = float(sys.argv[4])
        notes = sys.argv[5] if len(sys.argv) > 5 else ""
        add_test(test_name, start, end, notes)

    elif cmd == "benchmark":
        if len(sys.argv) < 3:
            available = [f.stem for f in BENCHMARK_DIR.glob("*.md")]
            print(f"Usage: python track_credits.py benchmark <scenario>")
            print(f"Available: {', '.join(sorted(available))}")
            sys.exit(1)
        run_benchmark(sys.argv[2])

    elif cmd == "estimate":
        kwargs = parse_estimate_args(sys.argv[2:])
        estimate_credits(**kwargs)

    elif cmd == "plan":
        kwargs = parse_plan_args(sys.argv[2:])
        plan_sprint(**kwargs)

    elif cmd == "baselines":
        show_baselines()

    elif cmd == "summary":
        period = None
        if "--period" in sys.argv and sys.argv.index("--period") + 1 < len(sys.argv):
            period = sys.argv[sys.argv.index("--period") + 1]
        show_summary(period)

    elif cmd == "export":
        export_markdown()

    elif cmd in ("help", "--help", "-h"):
        print_usage()

    else:
        print(f"Unknown command: {cmd}")
        print_usage()
        sys.exit(1)
