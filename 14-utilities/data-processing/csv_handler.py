"""
csv_handler.py

CSV data handling utilities.

Prerequisites:
- csv (stdlib)
"""

import csv
import io
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def read_csv(filepath: str, delimiter: str = ',') -> List[Dict[str, str]]:
    """
    Read a CSV file into a list of dictionaries.

    Interview Question:
        Q: CSV vs JSON vs Parquet — when to use each?
        A: CSV: human-readable, spreadsheet-compatible, no nesting.
           JSON: nested data, API responses, config files.
           Parquet: columnar, compressed, analytics/big data.
           CSV pitfalls: escaping commas in values, encoding issues,
           no type info (everything is string).
    """
    with open(filepath, newline='') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        return list(reader)


def write_csv(
    filepath: str,
    rows: List[Dict[str, Any]],
    fieldnames: List[str] = None,
    delimiter: str = ','
) -> int:
    """Write a list of dictionaries to a CSV file."""
    if not rows:
        return 0
    fieldnames = fieldnames or list(rows[0].keys())
    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def csv_to_markdown_table(rows: List[Dict[str, str]]) -> str:
    """Convert CSV rows to a Markdown table."""
    if not rows:
        return ''
    headers = list(rows[0].keys())
    lines = ['| ' + ' | '.join(headers) + ' |']
    lines.append('| ' + ' | '.join('---' for _ in headers) + ' |')
    for row in rows:
        lines.append('| ' + ' | '.join(str(row.get(h, '')) for h in headers) + ' |')
    return '\n'.join(lines)


def filter_csv(
    rows: List[Dict[str, str]],
    column: str,
    value: str
) -> List[Dict[str, str]]:
    """Filter CSV rows by column value."""
    return [row for row in rows if row.get(column) == value]


if __name__ == "__main__":
    rows = [
        {'service': 'api', 'status': 'up', 'latency_ms': '45'},
        {'service': 'db', 'status': 'up', 'latency_ms': '12'},
        {'service': 'cache', 'status': 'down', 'latency_ms': 'N/A'},
    ]
    print(csv_to_markdown_table(rows))
