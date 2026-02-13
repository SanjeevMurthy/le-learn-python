"""
json_processor.py

JSON data processing utilities.

Prerequisites:
- Standard library
"""

import json
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def flatten_json(data: Dict[str, Any], prefix: str = '') -> Dict[str, Any]:
    """
    Flatten nested JSON into dot-notation keys.

    Interview Question:
        Q: How do you process large JSON files efficiently?
        A: 1. Streaming parser (ijson): process without loading all in memory
           2. jq for CLI transformations
           3. json.loads for small files, ijson for large
           4. Flatten for log/metric ingestion
           5. JSON Lines (JSONL): one JSON per line for streaming
    """
    result = {}
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            result.update(flatten_json(value, full_key))
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if isinstance(item, dict):
                    result.update(flatten_json(item, f"{full_key}[{i}]"))
                else:
                    result[f"{full_key}[{i}]"] = item
        else:
            result[full_key] = value
    return result


def json_diff(a: Dict, b: Dict, path: str = '') -> List[Dict[str, Any]]:
    """Compare two JSON objects and return differences."""
    diffs = []
    all_keys = set(list(a.keys()) + list(b.keys()))

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key
        if key not in a:
            diffs.append({'path': current_path, 'type': 'added', 'value': b[key]})
        elif key not in b:
            diffs.append({'path': current_path, 'type': 'removed', 'value': a[key]})
        elif isinstance(a[key], dict) and isinstance(b[key], dict):
            diffs.extend(json_diff(a[key], b[key], current_path))
        elif a[key] != b[key]:
            diffs.append({'path': current_path, 'type': 'changed', 'old': a[key], 'new': b[key]})

    return diffs


def process_jsonl(filepath: str, filter_fn=None) -> List[Dict]:
    """Process a JSON Lines file with optional filtering."""
    results = []
    with open(filepath) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if filter_fn is None or filter_fn(record):
                    results.append(record)
            except json.JSONDecodeError as e:
                logger.warning(f"Line {line_num}: Invalid JSON — {e}")
    return results


if __name__ == "__main__":
    nested = {'server': {'host': 'db.example.com', 'port': 5432}, 'tags': ['prod', 'us-east']}
    flat = flatten_json(nested)
    print(f"  Flattened: {flat}")

    old = {'version': '1.0', 'replicas': 3}
    new = {'version': '1.1', 'replicas': 3, 'canary': True}
    diffs = json_diff(old, new)
    for d in diffs:
        print(f"  {d['type']}: {d['path']}")
