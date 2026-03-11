#!/usr/bin/env python3
"""
Validates REST API tests.
Usage: python validate_api_tests.py <TestClassName> [--base-url http://localhost:8080]
"""

import argparse
import sys
sys.path.insert(0, '../../shared-test-runner')
from run_tests import detect_build_tool, run_tests, report

parser = argparse.ArgumentParser(description='Validate REST API tests')
parser.add_argument('test_class', help='Test class name')
parser.add_argument('--base-url', help='API base URL (e.g., http://localhost:8080)')
args = parser.parse_args()

extra = []
if args.base_url:
    build = detect_build_tool()
    flag = '-D' if build == 'maven' else '-P'
    extra.append(f'{flag}API_BASE_URL={args.base_url}')
    print(f"Base URL: {args.base_url}")

print(f"Running API tests: {args.test_class}")
result = run_tests(args.test_class, extra_args=extra or None, timeout=60)
report(args.test_class, result)
