#!/usr/bin/env python3
"""
Shared test runner for Maven/Gradle projects.
Used by all three skill validation scripts.
"""

import subprocess
import sys
from pathlib import Path


def detect_build_tool():
    """Detect Maven or Gradle."""
    if Path('pom.xml').exists():
        return 'maven'
    if Path('build.gradle').exists() or Path('build.gradle.kts').exists():
        return 'gradle'
    return None


def run_tests(test_class, extra_args=None, timeout=120):
    """Run tests via Maven or Gradle. Returns dict with success, output, errors."""
    build_tool = detect_build_tool()
    if not build_tool:
        return {'success': False, 'errors': 'No build tool found (pom.xml or build.gradle)'}

    if build_tool == 'maven':
        cmd = ['mvn', 'test', f'-Dtest={test_class}']
    else:
        cmd = ['./gradlew', 'test', '--tests', test_class]

    if extra_args:
        cmd.extend(extra_args)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return {
            'success': result.returncode == 0,
            'output': result.stdout,
            'errors': result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {'success': False, 'errors': f'Test execution timeout ({timeout}s)'}
    except FileNotFoundError:
        return {'success': False, 'errors': f'{build_tool.capitalize()} not found. Install it first.'}


def report(test_class, result, hints=None):
    """Print result and exit with appropriate code."""
    if result['success']:
        print(f"All tests in {test_class} passed!")
        sys.exit(0)
    else:
        print(f"Tests failed:\n{result['errors']}")
        if hints:
            print("\nTroubleshooting:")
            for h in hints:
                print(f"- {h}")
        sys.exit(1)
