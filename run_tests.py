#!/usr/bin/env python3
"""
Test Runner Script for Synthetic Financial Data Generator

Provides easy commands to run different categories of tests with appropriate configurations.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description=None):
    """Run a command and handle output."""
    if description:
        print(f"\n🧪 {description}")
        print("=" * (len(description) + 4))
    
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"✅ {description or 'Command'} completed successfully")
    else:
        print(f"❌ {description or 'Command'} failed with exit code {result.returncode}")
    
    return result.returncode == 0


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = "pytest tests/unit/ -m unit"
    
    if verbose:
        cmd += " -v"
    
    if coverage:
        cmd += " --cov=scripts --cov=lib --cov=setup --cov-report=html --cov-report=term-missing"
    
    return run_command(cmd, "Running Unit Tests")


def run_integration_tests(verbose=False, elasticsearch=False, gemini=False):
    """Run integration tests."""
    cmd = "pytest tests/integration/ -m integration"
    
    # Add markers to exclude external dependencies if not requested
    markers = []
    if not elasticsearch:
        markers.append("not elasticsearch")
    if not gemini:
        markers.append("not gemini")
    
    if markers:
        cmd += f" -m 'integration and {' and '.join(markers)}'"
    
    if verbose:
        cmd += " -v"
    
    return run_command(cmd, "Running Integration Tests")


def run_functional_tests(verbose=False, elasticsearch=False, gemini=False):
    """Run functional tests."""
    cmd = "pytest tests/functional/ -m functional"
    
    # Add markers to exclude external dependencies if not requested
    markers = []
    if not elasticsearch:
        markers.append("not elasticsearch")
    if not gemini:
        markers.append("not gemini")
    
    if markers:
        cmd += f" -m 'functional and {' and '.join(markers)}'"
    
    if verbose:
        cmd += " -v"
    
    return run_command(cmd, "Running Functional Tests")


def run_all_tests(verbose=False, coverage=False, external=False):
    """Run all tests."""
    success = True
    
    print("🚀 Running Complete Test Suite")
    print("=" * 35)
    
    # Unit tests (always run)
    if not run_unit_tests(verbose=verbose, coverage=coverage):
        success = False
    
    # Integration tests
    if not run_integration_tests(verbose=verbose, elasticsearch=external, gemini=external):
        success = False
    
    # Functional tests  
    if not run_functional_tests(verbose=verbose, elasticsearch=external, gemini=external):
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check output above.")
    
    return success


def run_code_quality_checks():
    """Run code quality checks."""
    success = True
    
    print("🔍 Running Code Quality Checks")
    print("=" * 32)
    
    # Black formatting check
    if not run_command("black --check --diff scripts/ lib/ tests/ setup.py", 
                      "Checking code formatting (Black)"):
        print("💡 Run 'black scripts/ lib/ tests/ setup.py' to fix formatting")
        success = False
    
    # Import sorting check
    if not run_command("isort --check-only --diff scripts/ lib/ tests/ setup.py",
                      "Checking import sorting (isort)"):
        print("💡 Run 'isort scripts/ lib/ tests/ setup.py' to fix imports")
        success = False
    
    # Linting
    if not run_command("flake8 scripts/ lib/ tests/ setup.py --max-line-length=100 --extend-ignore=E203,W503",
                      "Linting code (flake8)"):
        success = False
    
    # Type checking (don't fail build on this initially)
    run_command("mypy scripts/ lib/ setup.py --ignore-missing-imports --no-strict-optional",
               "Type checking (mypy)")
    
    return success


def run_security_checks():
    """Run security checks."""
    success = True
    
    print("🔒 Running Security Checks")
    print("=" * 27)
    
    # Dependency vulnerability scan
    if not run_command("safety check", "Checking dependencies for vulnerabilities (safety)"):
        print("⚠️  Some dependencies have known vulnerabilities")
        # Don't fail build on this initially
    
    # Security linting
    if not run_command("bandit -r scripts/ lib/ setup.py", "Security linting (bandit)"):
        print("⚠️  Some security issues found")
        # Don't fail build on this initially
    
    return success


def run_specific_tests(test_path, verbose=False):
    """Run specific test file or directory."""
    cmd = f"pytest {test_path}"
    
    if verbose:
        cmd += " -v"
    
    return run_command(cmd, f"Running tests from {test_path}")


def check_dependencies():
    """Check that testing dependencies are installed."""
    try:
        import pytest
        import pytest_cov
        print("✅ Core testing dependencies available")
    except ImportError as e:
        print(f"❌ Missing testing dependency: {e}")
        print("💡 Install with: pip install -r requirements-test.txt")
        return False
    
    # Check optional dependencies
    optional_deps = {
        'black': 'black',
        'isort': 'isort', 
        'flake8': 'flake8',
        'mypy': 'mypy',
        'safety': 'safety',
        'bandit': 'bandit'
    }
    
    missing_optional = []
    for package, import_name in optional_deps.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_optional.append(package)
    
    if missing_optional:
        print(f"⚠️  Optional dependencies missing: {', '.join(missing_optional)}")
        print("💡 Install with: pip install -r requirements-test.txt")
    
    return True


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for Synthetic Financial Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --unit                    # Run only unit tests
  python run_tests.py --integration             # Run integration tests
  python run_tests.py --functional              # Run functional tests
  python run_tests.py --all                     # Run all tests (no external deps)
  python run_tests.py --all --external          # Run all tests including external deps
  python run_tests.py --quality                 # Run code quality checks
  python run_tests.py --security                # Run security checks
  python run_tests.py --specific tests/unit/test_setup.py  # Run specific test file
  
  # With options:
  python run_tests.py --unit --verbose --coverage
  python run_tests.py --integration --elasticsearch --gemini
        """
    )
    
    # Test categories
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--functional', action='store_true', help='Run functional tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    # Quality and security
    parser.add_argument('--quality', action='store_true', help='Run code quality checks')
    parser.add_argument('--security', action='store_true', help='Run security checks')
    
    # Specific test path
    parser.add_argument('--specific', type=str, help='Run specific test file or directory')
    
    # Options
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--external', action='store_true', 
                       help='Include tests requiring external dependencies (ES, Gemini)')
    parser.add_argument('--elasticsearch', action='store_true', 
                       help='Include Elasticsearch-dependent tests')
    parser.add_argument('--gemini', action='store_true', 
                       help='Include Gemini API-dependent tests')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    success = True
    
    # Determine what to run
    if args.all:
        success = run_all_tests(
            verbose=args.verbose, 
            coverage=args.coverage, 
            external=args.external
        )
    elif args.unit:
        success = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    elif args.integration:
        success = run_integration_tests(
            verbose=args.verbose, 
            elasticsearch=args.elasticsearch or args.external,
            gemini=args.gemini or args.external
        )
    elif args.functional:
        success = run_functional_tests(
            verbose=args.verbose,
            elasticsearch=args.elasticsearch or args.external, 
            gemini=args.gemini or args.external
        )
    elif args.quality:
        success = run_code_quality_checks()
    elif args.security:
        success = run_security_checks()
    elif args.specific:
        success = run_specific_tests(args.specific, verbose=args.verbose)
    else:
        # Default: run unit tests
        print("No test category specified. Running unit tests by default.")
        print("Use --help to see all options.")
        success = run_unit_tests(verbose=args.verbose, coverage=args.coverage)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()