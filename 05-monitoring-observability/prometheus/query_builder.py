"""
query_builder.py

PromQL query builder for common SRE metrics.

Prerequisites:
- Standard library only
"""

import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def error_rate(
    total_metric: str = 'http_requests_total',
    error_codes: str = '5..',
    window: str = '5m',
    job: Optional[str] = None
) -> str:
    """
    Build a PromQL query for error rate.

    Interview Question:
        Q: What are the four golden signals?
        A: 1. Latency — time to serve a request
           2. Traffic — demand on the system (RPS)
           3. Errors — rate of failed requests
           4. Saturation — how "full" the system is
           From Google SRE book. For each signal, set SLIs
           (measurements) and SLOs (targets). Alert on SLO burn rate.
    """
    labels = f'status_code=~"{error_codes}"'
    if job:
        labels += f',job="{job}"'

    query = (
        f'sum(rate({total_metric}{{{labels}}}[{window}])) / '
        f'sum(rate({total_metric}[{window}])) * 100'
    )
    return query


def latency_percentile(
    histogram: str = 'http_request_duration_seconds',
    percentile: float = 0.99,
    window: str = '5m',
    job: Optional[str] = None
) -> str:
    """Build a PromQL query for latency percentiles (from histogram)."""
    labels = f'job="{job}"' if job else ''
    return (
        f'histogram_quantile({percentile}, '
        f'sum(rate({histogram}_bucket{{{labels}}}[{window}])) by (le))'
    )


def saturation_query(
    resource: str = 'cpu',
    instance: Optional[str] = None
) -> str:
    """Build saturation queries for common resources."""
    queries = {
        'cpu': 'avg(1 - rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100',
        'memory': '(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100',
        'disk': '(1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100',
    }
    query = queries.get(resource, queries['cpu'])
    if instance:
        query = query.replace('{', f'{{instance="{instance}",', 1) if '{' in query else query
    return query


def slo_burn_rate(
    error_metric: str,
    slo_target: float = 0.999,
    windows: str = '1h'
) -> str:
    """
    Build SLO burn rate query for multi-window alerting.

    Interview Question:
        Q: What is SLO-based alerting?
        A: Instead of threshold-based alerts (CPU > 80%), alert on
           error budget burn rate. If SLO=99.9% (error budget=0.1%/month),
           track how fast you're consuming the budget.
           Multi-window: 1h burn rate > 14x (exhausts budget in ~2 days),
           6h burn rate > 6x. This reduces alert noise while catching
           real issues. Google SRE workbook Chapter 5.
    """
    error_budget = 1 - slo_target
    return (
        f'sum(rate({error_metric}[{windows}])) / {error_budget}'
    )


if __name__ == "__main__":
    print("PromQL Query Builder — Generated Queries")
    print(f"  Error rate: {error_rate(job='api-server')}")
    print(f"  P99 latency: {latency_percentile(percentile=0.99)}")
    print(f"  CPU saturation: {saturation_query('cpu')}")
    print(f"  SLO burn rate: {slo_burn_rate('http_errors_total')}")
