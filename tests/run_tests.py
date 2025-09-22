#!/usr/bin/env python3
"""
Test Runner for PyRedactor Application
"""

import sys
import os

# Add the parent directory to the python path to allow imports from PyRedactor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import subprocess
import argparse


def run_unit_tests():
    """Run unit tests"""
    print("Running unit tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "unit", 
            "-v", 
            "--tb=short"
        ], cwd=os.path.dirname(os.path.abspath(__file__)), check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running unit tests: {e}")
        return False


def run_integration_tests():
    """Run integration tests"""
    print("Running integration tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "integration", 
            "-v", 
            "--tb=short"
        ], cwd=os.path.dirname(os.path.abspath(__file__)), check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running integration tests: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("Running all tests...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            ".", 
            "-v", 
            "--tb=short"
        ], cwd=os.path.dirname(os.path.abspath(__file__)), check=False)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running all tests: {e}")
        return False


def run_syntax_check():
    """Run syntax check on all source files"""
    print("Running syntax check...")
    try:
        # Find all Python files
        py_files = []
        for root, dirs, files in os.walk("."):
            for file in files:
                if file.endswith(".py") and not file.startswith("test_"):
                    py_files.append(os.path.join(root, file))
        
        # Compile each file
        success = True
        for py_file in py_files:
            try:
                result = subprocess.run([
                    sys.executable, "-m", "py_compile", py_file
                ], cwd=os.path.dirname(os.path.abspath(__file__)), check=False, capture_output=True)
                if result.returncode != 0:
                    print(f"Syntax error in {py_file}:")
                    print(result.stderr.decode())
                    success = False
            except Exception as e:
                print(f"Error checking syntax for {py_file}: {e}")
                success = False
        
        return success
    except Exception as e:
        print(f"Error running syntax check: {e}")
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="PyRedactor Test Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--syntax", action="store_true", help="Run syntax check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # If no arguments specified, run all tests
    if not any([args.unit, args.integration, args.all, args.syntax]):
        args.all = True
    
    success = True
    
    if args.syntax:
        success &= run_syntax_check()
    
    if args.unit:
        success &= run_unit_tests()
    
    if args.integration:
        success &= run_integration_tests()
    
    if args.all:
        success &= run_all_tests()
    
    if success:
        print("\nAll tests passed!")
        return 0
    else:
        print("\nSome tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())