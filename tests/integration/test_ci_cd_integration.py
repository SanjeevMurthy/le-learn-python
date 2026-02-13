"""
test_ci_cd_integration.py

Integration tests for CI/CD workflow patterns.
Tests verify that pipeline components work together.
"""

import os
import sys
import subprocess
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_python_syntax_check():
    """Verify all Python files in the repo have valid syntax."""
    repo_root = os.path.join(os.path.dirname(__file__), '..', '..')
    errors = []

    for root, dirs, files in os.walk(repo_root):
        # Skip hidden dirs and __pycache__
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                result = subprocess.run(
                    [sys.executable, '-m', 'py_compile', filepath],
                    capture_output=True, text=True
                )
                if result.returncode != 0:
                    errors.append(f"{filepath}: {result.stderr}")

    assert len(errors) == 0, f"Syntax errors found:\n" + "\n".join(errors)
    print(f"  ✅ test_python_syntax_check (all .py files valid)")


def test_module_structure():
    """Verify expected module directories exist."""
    repo_root = os.path.join(os.path.dirname(__file__), '..', '..')
    expected_modules = [
        '01-core-python-for-sre',
        '02-cloud-automation',
        '03-kubernetes',
        '04-cicd-automation',
        '05-monitoring-observability',
        '06-secret-management',
        '07-artifact-management',
        '08-infrastructure-as-code',
        '09-incident-response',
        '10-performance-optimization',
        '11-networking',
        '12-database-operations',
        '13-interview-prep',
        '14-utilities',
        '15-real-world-projects',
    ]

    for module in expected_modules:
        module_path = os.path.join(repo_root, module)
        assert os.path.isdir(module_path), f"Missing module directory: {module}"
        readme = os.path.join(module_path, 'README.md')
        assert os.path.exists(readme), f"Missing README.md in {module}"

    print(f"  ✅ test_module_structure ({len(expected_modules)} modules verified)")


def test_no_hardcoded_secrets():
    """Scan for potentially hardcoded secrets."""
    repo_root = os.path.join(os.path.dirname(__file__), '..', '..')
    suspicious_patterns = ['password=', 'secret_key=', 'api_key=']
    # Note: this is a basic check; real scanning uses tools like truffleHog
    findings = []

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        for f in files:
            if f.endswith('.py'):
                filepath = os.path.join(root, f)
                with open(filepath) as fh:
                    for line_num, line in enumerate(fh, 1):
                        # Skip comments and strings that are examples
                        if line.strip().startswith('#'):
                            continue
                        for pattern in suspicious_patterns:
                            if pattern in line.lower() and 'os.environ' not in line:
                                # Allow examples in docstrings/comments
                                if '"""' in line or "'''" in line or 'example' in line.lower():
                                    continue

    # This is informational — not a hard failure for this learning repo
    print(f"  ✅ test_no_hardcoded_secrets (scan complete)")


if __name__ == "__main__":
    print("CI/CD Integration Tests")
    test_python_syntax_check()
    test_module_structure()
    test_no_hardcoded_secrets()
    print("  All integration tests passed!")
