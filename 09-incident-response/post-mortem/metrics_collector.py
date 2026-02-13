"""
metrics_collector.py

Collect metrics during and after incidents for analysis.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def collect_prometheus_metrics(
    queries: Dict[str, str],
    start: str,
    end: str,
    step: str = '60s'
) -> Dict[str, Any]:
    """
    Collect Prometheus metrics for an incident window.

    Interview Question:
        Q: What metrics do you collect during a post-mortem?
        A: Golden signals: latency, traffic, errors, saturation.
           System: CPU, memory, disk, network I/O.
           Application: request count, error rate, response time.
           Dependencies: DB query time, cache hit rate, external API latency.
           Deployment: deploy events, config changes.
           The goal: correlate events with metric changes.
    """
    prom_url = os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')
    results = {}

    for name, query in queries.items():
        response = requests.get(
            f'{prom_url}/api/v1/query_range',
            params={'query': query, 'start': start, 'end': end, 'step': step}
        )

        if response.status_code == 200:
            data = response.json().get('data', {}).get('result', [])
            results[name] = {
                'query': query,
                'series_count': len(data),
                'data_points': sum(len(s.get('values', [])) for s in data),
            }
        else:
            results[name] = {'error': response.text}

    return results


def summarize_incident_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Summarize collected metrics for a report."""
    return {
        'metrics_collected': len(metrics),
        'total_data_points': sum(
            m.get('data_points', 0) for m in metrics.values()
        ),
        'queries': list(metrics.keys()),
    }


if __name__ == "__main__":
    print("Metrics Collector — Usage Examples")
    print("""
    queries = {
        'error_rate': 'rate(http_requests_total{status=~"5.."}[5m])',
        'latency_p99': 'histogram_quantile(0.99, rate(http_duration_seconds_bucket[5m]))',
        'cpu_usage': 'avg(rate(process_cpu_seconds_total[5m]))',
    }
    metrics = collect_prometheus_metrics(
        queries,
        start='2024-01-15T14:00:00Z',
        end='2024-01-15T16:00:00Z'
    )
    """)
