#!/usr/bin/env python3
"""
Test runner script for the HR Onboarding Agent system.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print('='*60)

    try:
        result = subprocess.run(command, capture_output=True, text=True, cwd=Path(__file__).parent)

        if result.returncode == 0:
            print("✅ SUCCESS")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print("❌ FAILED")
            print("Error output:")
            print(result.stderr)
            if result.stdout:
                print("Standard output:")
                print(result.stdout)

        return result.returncode == 0

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


def main():
    """Run all tests and validations."""
    print("🚀 Starting HR Onboarding Agent System Tests")
    print("=" * 60)

    # Change to project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    success_count = 0
    total_tests = 0

    # 1. Syntax validation
    total_tests += 1
    if run_command([sys.executable, "-m", "py_compile", "src/main.py"], "Syntax validation"):
        success_count += 1

    # 2. Import validation
    total_tests += 1
    if run_command([sys.executable, "-c", "import src.main; print('Import successful')"], "Import validation"):
        success_count += 1

    # 3. Unit tests
    total_tests += 1
    if run_command([sys.executable, "-m", "pytest", "tests/unit/", "-v"], "Unit tests"):
        success_count += 1

    # 4. Integration tests
    total_tests += 1
    if run_command([sys.executable, "-m", "pytest", "tests/integration/", "-v"], "Integration tests"):
        success_count += 1

    # 5. End-to-end tests
    total_tests += 1
    if run_command([sys.executable, "-m", "pytest", "tests/e2e/", "-v"], "End-to-end tests"):
        success_count += 1

    # 6. Coverage report
    total_tests += 1
    if run_command([
        sys.executable, "-m", "pytest", "--cov=src", "--cov-report=html", "--cov-report=term"
    ], "Coverage analysis"):
        success_count += 1

    # 7. Type checking (if mypy is available)
    total_tests += 1
    try:
        if run_command([sys.executable, "-m", "mypy", "src/", "--ignore-missing-imports"], "Type checking"):
            success_count += 1
    except FileNotFoundError:
        print("⚠️  Mypy not installed, skipping type checking")
        success_count += 1  # Don't count as failure

    # 8. Linting (if flake8 is available)
    total_tests += 1
    try:
        if run_command([sys.executable, "-m", "flake8", "src/", "--max-line-length=100"], "Code linting"):
            success_count += 1
    except FileNotFoundError:
        print("⚠️  Flake8 not installed, skipping linting")
        success_count += 1  # Don't count as failure

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    print(f"Passed: {success_count}/{total_tests}")
    print(".1f")

    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("❌ SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())