"""
log_correlation.py

Correlate logs across services using request IDs and timestamps.

Prerequisites:
- Standard library only
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def correlate_by_request_id(
    logs: List[Dict[str, Any]],
    request_id_field: str = 'request_id'
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group logs by request ID to trace a request across services.

    Interview Question:
        Q: How does distributed tracing work?
        A: Three pillars of observability: metrics, logs, traces.
           Tracing: propagate a trace ID across service boundaries.
           Each service generates spans (operations with start/end).
           Spans form a tree showing the request flow.
           Standards: OpenTelemetry (W3C Trace Context headers).
           Tools: Jaeger, Zipkin, AWS X-Ray, Datadog APM.
           Correlation: embed trace_id in logs for log-to-trace linking.
    """
    grouped = defaultdict(list)
    for log in logs:
        req_id = log.get(request_id_field)
        if req_id:
            grouped[req_id].append(log)

    # Sort each group by timestamp
    for req_id in grouped:
        grouped[req_id].sort(key=lambda x: x.get('timestamp', ''))

    logger.info(f"Correlated {len(logs)} logs into {len(grouped)} request groups")
    return dict(grouped)


def find_slow_requests(
    correlated_logs: Dict[str, List[Dict[str, Any]]],
    threshold_ms: float = 1000.0,
    duration_field: str = 'duration_ms'
) -> List[Dict[str, Any]]:
    """Find requests that exceeded a duration threshold."""
    slow = []
    for req_id, logs in correlated_logs.items():
        # Look for a log entry with duration
        for log in logs:
            duration = log.get(duration_field)
            if duration and float(duration) > threshold_ms:
                slow.append({
                    'request_id': req_id,
                    'duration_ms': float(duration),
                    'service': log.get('service', 'unknown'),
                    'log_count': len(logs),
                })
                break
    return sorted(slow, key=lambda x: x['duration_ms'], reverse=True)


def find_error_chains(
    correlated_logs: Dict[str, List[Dict[str, Any]]],
    error_level: str = 'ERROR'
) -> List[Dict[str, Any]]:
    """Find requests that produced errors across multiple services."""
    error_chains = []
    for req_id, logs in correlated_logs.items():
        error_logs = [l for l in logs if l.get('level', '').upper() == error_level]
        if len(error_logs) > 1:
            services = list({l.get('service', 'unknown') for l in error_logs})
            error_chains.append({
                'request_id': req_id,
                'error_count': len(error_logs),
                'affected_services': services,
                'first_error': error_logs[0].get('message', ''),
            })
    return error_chains


if __name__ == "__main__":
    print("Log Correlation — Usage Examples")
    print("""
    logs = [
        {'request_id': 'abc123', 'service': 'gateway', 'level': 'INFO', ...},
        {'request_id': 'abc123', 'service': 'api', 'level': 'ERROR', ...},
    ]
    grouped = correlate_by_request_id(logs)
    slow = find_slow_requests(grouped, threshold_ms=500)
    errors = find_error_chains(grouped)
    """)
