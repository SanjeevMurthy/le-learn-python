"""
solution.py — Log Parser Implementation
"""

import re
import json
from collections import Counter, defaultdict
from typing import Dict, Any, List, Iterator, Optional


# Nginx/Apache combined log format regex
ACCESS_LOG_RE = re.compile(
    r'(?P<ip>[\d.]+)\s+\S+\s+\S+\s+'
    r'\[(?P<timestamp>[^\]]+)\]\s+'
    r'"(?P<method>\w+)\s+(?P<path>\S+)\s+\S+"\s+'
    r'(?P<status>\d+)\s+(?P<bytes>\d+)'
    r'(?:\s+(?P<response_time>[\d.]+))?'
)


def parse_access_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a single access log line."""
    match = ACCESS_LOG_RE.match(line.strip())
    if not match:
        return None
    return {
        'ip': match.group('ip'),
        'timestamp': match.group('timestamp'),
        'method': match.group('method'),
        'path': match.group('path'),
        'status': int(match.group('status')),
        'bytes': int(match.group('bytes')),
        'response_time': float(match.group('response_time')) if match.group('response_time') else None,
    }


def parse_json_log_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse a JSON-formatted log line."""
    try:
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def stream_parse(filepath: str, fmt: str = 'access') -> Iterator[Dict[str, Any]]:
    """Stream-parse a log file line by line."""
    parser = parse_access_log_line if fmt == 'access' else parse_json_log_line
    with open(filepath) as f:
        for line in f:
            parsed = parser(line)
            if parsed:
                yield parsed


def analyze_logs(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze parsed log entries and return metrics."""
    if not entries:
        return {'total': 0}

    total = len(entries)
    status_counts = Counter(e['status'] for e in entries)
    errors = sum(v for k, v in status_counts.items() if k >= 400)

    # Response time percentiles
    response_times = sorted(
        e['response_time'] for e in entries if e.get('response_time') is not None
    )

    percentiles = {}
    if response_times:
        for p in [50, 95, 99]:
            idx = int(len(response_times) * p / 100)
            percentiles[f'p{p}'] = round(response_times[min(idx, len(response_times) - 1)], 3)

    # Top error paths
    error_paths = Counter(
        (e['path'], e['status']) for e in entries if e['status'] >= 400
    )

    return {
        'total_requests': total,
        'error_rate': round(errors / total, 4),
        'status_distribution': dict(status_counts.most_common(10)),
        'response_time_percentiles': percentiles,
        'top_errors': [
            {'path': path, 'status': status, 'count': count}
            for (path, status), count in error_paths.most_common(10)
        ],
        'unique_ips': len(set(e.get('ip', '') for e in entries)),
    }


def detect_anomalies(
    entries: List[Dict[str, Any]], error_threshold: float = 0.1
) -> List[Dict[str, Any]]:
    """Detect anomalies in log data."""
    anomalies = []
    total = len(entries)
    if total == 0:
        return anomalies

    errors = sum(1 for e in entries if e.get('status', 0) >= 500)
    error_rate = errors / total
    if error_rate > error_threshold:
        anomalies.append({
            'type': 'high_error_rate',
            'value': round(error_rate, 4),
            'threshold': error_threshold,
        })

    # Slow request detection
    slow = [e for e in entries if (e.get('response_time') or 0) > 5.0]
    if len(slow) > total * 0.05:
        anomalies.append({
            'type': 'high_slow_request_rate',
            'count': len(slow),
            'percentage': round(len(slow) / total * 100, 1),
        })

    return anomalies


if __name__ == "__main__":
    # Demo with synthetic data
    entries = [
        {'ip': '10.0.0.1', 'path': '/api/users', 'status': 200, 'response_time': 0.05},
        {'ip': '10.0.0.2', 'path': '/api/orders', 'status': 500, 'response_time': 2.3},
        {'ip': '10.0.0.1', 'path': '/api/users', 'status': 200, 'response_time': 0.03},
        {'ip': '10.0.0.3', 'path': '/api/auth', 'status': 401, 'response_time': 0.01},
    ]
    result = analyze_logs(entries)
    print(f"Total: {result['total_requests']}, Error rate: {result['error_rate']}")
