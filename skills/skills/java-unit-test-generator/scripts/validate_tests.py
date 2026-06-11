#!/usr/bin/env python3
"""
Validates generated JUnit tests.
Usage: python validate_tests.py <TestClassName>
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'shared', 'test-runner'))
from run_tests import run_tests, report

if len(sys.argv) < 2:
    print("Usage: python validate_tests.py <TestClassName>")
    sys.exit(1)

test_class = sys.argv[1]
print(f"Running {test_class}...")
result = run_tests(test_class, timeout=60)
report(test_class, result)
