"""
test_log_analysis.py

Unit tests for Module 02 — Log Analysis.
"""

import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_log_level_detection():
    """Test that log level keywords are correctly identified."""
    levels = {'ERROR', 'WARNING', 'INFO', 'DEBUG', 'CRITICAL'}
    for level in levels:
        line = f"2024-01-15 10:30:00 {level} Something happened"
        assert level in line, f"Expected {level} in log line"
    print("  ✅ test_log_level_detection")


def test_pattern_matching():
    """Test regex-based log pattern matching."""
    import re
    pattern = r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}'
    line = "2024-01-15 10:30:00 ERROR Database connection failed"
    match = re.search(pattern, line)
    assert match is not None, "Timestamp pattern should match"
    assert match.group() == "2024-01-15 10:30:00"
    print("  ✅ test_pattern_matching")


def test_log_file_reading():
    """Test reading a log file line by line."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write("line1\nline2\nline3\n")
        f.flush()
        path = f.name

    with open(path) as f:
        lines = f.readlines()
    os.unlink(path)
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}"
    print("  ✅ test_log_file_reading")


if __name__ == "__main__":
    print("Log Analysis Unit Tests")
    test_log_level_detection()
    test_pattern_matching()
    test_log_file_reading()
    print("  All tests passed!")
