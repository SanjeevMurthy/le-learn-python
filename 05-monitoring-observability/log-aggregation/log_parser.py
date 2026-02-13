"""
log_parser.py

Parse and structure various log formats.

Prerequisites:
- Standard library only
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common log format patterns
PATTERNS = {
    'nginx': re.compile(
        r'(?P<ip>[\d.]+) - (?P<user>\S+) \[(?P<timestamp>[^\]]+)\] '
        r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>\S+)" '
        r'(?P<status>\d+) (?P<bytes>\d+)'
    ),
    'syslog': re.compile(
        r'(?P<timestamp>\w+\s+\d+\s+[\d:]+) (?P<hostname>\S+) '
        r'(?P<process>\S+?)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)'
    ),
    'python': re.compile(
        r'(?P<timestamp>[\d-]+\s+[\d:,]+)\s+-\s+(?P<logger>\S+)\s+-\s+'
        r'(?P<level>\S+)\s+-\s+(?P<message>.*)'
    ),
}


def parse_log_line(line: str, format_name: str = '') -> Optional[Dict[str, Any]]:
    """
    Parse a log line into structured fields.

    Interview Question:
        Q: Why is structured logging important?
        A: Unstructured logs (free-text) are hard to search, filter,
           and aggregate. Structured logging (JSON) enables:
           1. Fast indexing and querying in Elasticsearch/Loki
           2. Easy correlation across services (request ID)
           3. Automated alert rules on specific fields
           4. Machine parsing for anomaly detection
           Standard fields: timestamp, level, service, request_id, message.
    """
    # Try JSON first
    try:
        return json.loads(line)
    except (json.JSONDecodeError, TypeError):
        pass

    # Try known patterns
    formats = [format_name] if format_name else PATTERNS.keys()
    for fmt in formats:
        pattern = PATTERNS.get(fmt)
        if pattern:
            match = pattern.match(line)
            if match:
                parsed = match.groupdict()
                parsed['_format'] = fmt
                return parsed

    # Fallback: return raw
    return {'message': line, '_format': 'raw'}


def parse_log_file(filepath: str, format_name: str = '') -> List[Dict[str, Any]]:
    """Parse all lines in a log file."""
    entries = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                parsed = parse_log_line(line, format_name)
                if parsed:
                    entries.append(parsed)
    logger.info(f"Parsed {len(entries)} entries from {filepath}")
    return entries


if __name__ == "__main__":
    print("Log Parser — Usage Examples")
    print("""
    # Parse a single line
    result = parse_log_line('192.168.1.1 - - [10/Oct/2000:13:55:36 -0700] "GET /index.html HTTP/1.0" 200 2326')
    print(f"  {result}")

    # Parse JSON logs
    result = parse_log_line('{"level":"error","service":"api","message":"timeout"}')
    print(f"  Level: {result['level']}, Service: {result['service']}")
    """)
