#!/usr/bin/env python3
"""
Validates Selenium UI tests.
Usage: python validate_ui_tests.py <TestClassName> [--headed]
"""

import argparse
import sys
sys.path.insert(0, '../../shared-test-runner')
from run_tests import detect_build_tool, run_tests, report

parser = argparse.ArgumentParser(description='Validate Selenium UI tests')
parser.add_argument('test_class', help='Test class name')
parser.add_argument('--headed', action='store_true', help='Run with visible browser (default: headless)')
args = parser.parse_args()

extra = []
if not args.headed:
    build = detect_build_tool()
    flag = '-D' if build == 'maven' else '-P'
    extra.append(f'{flag}headless=true')

mode = 'Headed' if args.headed else 'Headless'
print(f"Running UI tests: {args.test_class} ({mode})")

result = run_tests(args.test_class, extra_args=extra or None, timeout=120)
report(args.test_class, result, hints=[
    "Check element selectors (data-testid preferred)",
    "Verify wait times are sufficient",
    "Run with --headed to see browser behavior",
])
