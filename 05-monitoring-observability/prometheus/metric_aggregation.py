"""
metric_aggregation.py

Aggregate and summarize Prometheus metrics for reporting.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, List

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')


def _query(promql: str) -> List[Dict[str, Any]]:
    """Execute a PromQL query and return results."""
    url = f'{_get_base_url()}/api/v1/query'
    response = requests.get(url, params={'query': promql})
    response.raise_for_status()
    data = response.json()
    return data['data'].get('result', [])


def get_service_summary(
    job: str,
    window: str = '5m'
) -> Dict[str, Any]:
    """
    Get a summary of key metrics for a service.

    Interview Question:
        Q: What are USE and RED methods?
        A: USE (for resources): Utilization, Saturation, Errors.
           Apply to infrastructure: CPU, memory, disk, network.
           RED (for services): Rate, Errors, Duration.
           Apply to request-driven services: APIs, microservices.
           USE → infrastructure health, RED → service health.
           Combined with golden signals for complete observability.
    """
    summary = {'job': job, 'window': window}

    # Request rate
    results = _query(f'sum(rate(http_requests_total{{job="{job}"}}[{window}]))')
    summary['request_rate'] = float(results[0]['value'][1]) if results else 0

    # Error rate
    results = _query(
        f'sum(rate(http_requests_total{{job="{job}",status_code=~"5.."}}[{window}]))'
        f' / sum(rate(http_requests_total{{job="{job}"}}[{window}])) * 100'
    )
    summary['error_rate_pct'] = round(float(results[0]['value'][1]), 2) if results else 0

    # P99 latency
    results = _query(
        f'histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{{job="{job}"}}[{window}])) by (le))'
    )
    summary['p99_latency_s'] = round(float(results[0]['value'][1]), 4) if results else 0

    return summary


if __name__ == "__main__":
    print("Metric Aggregation — Usage Examples")
    print("""
    summary = get_service_summary('api-server')
    print(f"  RPS: {summary['request_rate']:.1f}")
    print(f"  Error rate: {summary['error_rate_pct']}%")
    print(f"  P99 latency: {summary['p99_latency_s']}s")
    """)
