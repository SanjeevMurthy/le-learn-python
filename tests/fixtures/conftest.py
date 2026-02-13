"""
conftest.py — Shared test fixtures.

Common fixtures for all test modules.
"""

import os
import sys
import tempfile


# Ensure project root is in path
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, PROJECT_ROOT)


def create_temp_file(content: str, suffix: str = '.txt') -> str:
    """Create a temporary file with given content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
        f.write(content)
        return f.name


def cleanup_temp_file(filepath: str) -> None:
    """Remove a temporary file."""
    if os.path.exists(filepath):
        os.unlink(filepath)


def sample_log_lines():
    """Return sample log lines for testing."""
    return [
        '2024-01-15 10:30:00 INFO Application started',
        '2024-01-15 10:30:01 WARNING High memory usage',
        '2024-01-15 10:30:02 ERROR Database connection failed',
        '2024-01-15 10:30:03 INFO Request processed',
        '2024-01-15 10:30:04 CRITICAL Disk full',
    ]


def sample_config():
    """Return a sample configuration dictionary."""
    return {
        'server': {
            'host': 'localhost',
            'port': 8080,
        },
        'database': {
            'host': 'db.example.com',
            'port': 5432,
            'name': 'myapp',
        },
        'logging': {
            'level': 'INFO',
            'format': 'json',
        },
    }
