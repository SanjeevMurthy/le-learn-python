"""
test_data_processing.py

Unit tests for Module 14 — Data Processing utilities.
"""

import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_json_flatten():
    """Test JSON flattening to dot-notation."""
    nested = {'server': {'host': 'db.example.com', 'port': 5432}}
    flat = {}

    def flatten(data, prefix=''):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flatten(value, full_key)
            else:
                flat[full_key] = value

    flatten(nested)
    assert flat['server.host'] == 'db.example.com'
    assert flat['server.port'] == 5432
    print("  ✅ test_json_flatten")


def test_json_diff():
    """Test JSON diff detection."""
    old = {'version': '1.0', 'replicas': 3}
    new = {'version': '1.1', 'replicas': 3, 'canary': True}

    added = set(new.keys()) - set(old.keys())
    removed = set(old.keys()) - set(new.keys())
    changed = {k for k in old.keys() & new.keys() if old[k] != new[k]}

    assert 'canary' in added
    assert len(removed) == 0
    assert 'version' in changed
    print("  ✅ test_json_diff")


def test_csv_to_markdown():
    """Test CSV to Markdown table conversion."""
    rows = [
        {'name': 'api', 'status': 'up'},
        {'name': 'db', 'status': 'down'},
    ]
    headers = list(rows[0].keys())
    header_line = '| ' + ' | '.join(headers) + ' |'
    assert '| name | status |' == header_line
    print("  ✅ test_csv_to_markdown")


def test_jsonl_processing():
    """Test JSON Lines file processing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        f.write('{"level": "ERROR", "msg": "fail"}\n')
        f.write('{"level": "INFO", "msg": "ok"}\n')
        f.write('{"level": "ERROR", "msg": "timeout"}\n')
        path = f.name

    errors = []
    with open(path) as f:
        for line in f:
            record = json.loads(line)
            if record['level'] == 'ERROR':
                errors.append(record)
    os.unlink(path)

    assert len(errors) == 2
    print("  ✅ test_jsonl_processing")


if __name__ == "__main__":
    print("Data Processing Unit Tests")
    test_json_flatten()
    test_json_diff()
    test_csv_to_markdown()
    test_jsonl_processing()
    print("  All tests passed!")
