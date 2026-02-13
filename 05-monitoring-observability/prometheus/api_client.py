"""
api_client.py

Prometheus HTTP API client for querying metrics.

Interview Topics:
- Prometheus architecture (pull model, TSDB, scrape)
- Instant vs range queries
- PromQL data types (vector, scalar, matrix)

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('PROMETHEUS_URL', 'http://localhost:9090')


def instant_query(query: str, time_val: Optional[str] = None) -> Dict[str, Any]:
    """
    Execute an instant PromQL query.

    Interview Question:
        Q: Explain the Prometheus architecture.
        A: Pull-based monitoring system:
           1. Prometheus server scrapes targets at configured intervals
           2. Targets expose /metrics endpoint in text format
           3. Data stored in local TSDB (time-series database)
           4. PromQL for querying time-series data
           5. AlertManager handles alert routing/dedup/silencing
           Components: Prometheus server, Alertmanager, Pushgateway
           (for batch jobs), exporters (node_exporter, etc.).
           Federation for multi-cluster setups. Thanos/Cortex/Mimir
           for long-term storage and global view.
    """
    url = f'{_get_base_url()}/api/v1/query'
    params = {'query': query}
    if time_val:
        params['time'] = time_val

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if data['status'] != 'success':
        logger.error(f"Query failed: {data.get('error', 'unknown')}")
        return {'status': 'error', 'error': data.get('error')}

    results = []
    for result in data['data'].get('result', []):
        results.append({
            'metric': result['metric'],
            'value': result['value'][1] if 'value' in result else None,
            'timestamp': result['value'][0] if 'value' in result else None,
        })

    logger.info(f"Query returned {len(results)} time series")
    return {'status': 'success', 'result_type': data['data']['resultType'], 'results': results}


def range_query(
    query: str,
    start: str,
    end: str,
    step: str = '60s'
) -> Dict[str, Any]:
    """
    Execute a range query returning data over a time window.

    Interview Question:
        Q: What's the difference between rate() and irate()?
        A: rate(): per-second average rate over the entire range.
           Smooths out spikes. Good for alerting.
           irate(): instant rate using last two data points.
           Shows spikes, good for dashboards.
           Rule of thumb: rate() for alerts, irate() for graphs.
           Both only work on counters (monotonically increasing).
    """
    url = f'{_get_base_url()}/api/v1/query_range'
    params = {'query': query, 'start': start, 'end': end, 'step': step}

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    results = []
    for result in data['data'].get('result', []):
        results.append({
            'metric': result['metric'],
            'values': [(v[0], float(v[1])) for v in result.get('values', [])],
        })

    return {'status': 'success', 'results': results}


def get_targets() -> List[Dict[str, Any]]:
    """Get scrape target status."""
    url = f'{_get_base_url()}/api/v1/targets'
    response = requests.get(url)
    response.raise_for_status()

    targets = []
    for t in response.json()['data'].get('activeTargets', []):
        targets.append({
            'job': t['labels'].get('job', 'N/A'),
            'instance': t['labels'].get('instance', 'N/A'),
            'health': t['health'],
            'last_scrape': t.get('lastScrape', ''),
        })
    return targets


if __name__ == "__main__":
    print("Prometheus API Client — Usage Examples")
    print("""
    # Instant query
    result = instant_query('up{job="node_exporter"}')

    # CPU usage rate
    result = instant_query('rate(node_cpu_seconds_total{mode="idle"}[5m])')

    # Range query for last hour
    result = range_query('rate(http_requests_total[5m])', 'now-1h', 'now', '60s')
    """)
