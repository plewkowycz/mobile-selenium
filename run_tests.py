#!/usr/bin/env python3
"""Simple test runner for local development."""

import subprocess
import sys
import os


def run_tests(headless=False, verbose=True):
    """Run tests with specified options."""
    cmd = ["source", ".venv/bin/activate", "&&"]
    
    # Add pytest command
    pytest_cmd = ["pytest"]
    
    if verbose:
        pytest_cmd.append("-v")
    
    if headless:
        os.environ["HEADLESS"] = "true"
    else:
        os.environ["HEADLESS"] = "false"
        pytest_cmd.append("-s")  # Show print statements
        
    pytest_cmd.extend(["--tb=short", "tests/"])
    
    # Combine and run
    full_cmd = " ".join(cmd + pytest_cmd)
    print(f"Running: {full_cmd}")
    
    result = subprocess.run(full_cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Twitch mobile tests")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--quiet", action="store_true", help="Run without verbose output")
    
    args = parser.parse_args()
    
    success = run_tests(headless=args.headless, verbose=not args.quiet)
    
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed!")
        sys.exit(1)
