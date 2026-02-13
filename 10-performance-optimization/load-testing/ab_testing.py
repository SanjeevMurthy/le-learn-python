"""
ab_testing.py

Apache Bench (ab) wrapper and load test analysis.

Prerequisites:
- subprocess (stdlib)
"""

import subprocess
import re
import logging
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_ab_test(
    url: str,
    requests_count: int = 1000,
    concurrency: int = 10,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Run Apache Bench load test.

    Interview Question:
        Q: What metrics matter in load testing?
        A: Latency: p50, p95, p99 (not just average — tail latency matters).
           Throughput: requests per second (RPS).
           Error rate: % of failed requests under load.
           Saturation: CPU, memory, connections at limit.
           Concurrency: how many parallel connections supported.
           Rule: "You're not done until p99 is acceptable."
    """
    cmd = ['ab', '-n', str(requests_count), '-c', str(concurrency), '-s', str(timeout), url]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        output = result.stdout

        # Parse key metrics
        metrics = {}
        patterns = {
            'rps': r'Requests per second:\s+([\d.]+)',
            'time_per_request': r'Time per request:\s+([\d.]+)',
            'transfer_rate': r'Transfer rate:\s+([\d.]+)',
            'failed_requests': r'Failed requests:\s+(\d+)',
            'complete_requests': r'Complete requests:\s+(\d+)',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                metrics[key] = float(match.group(1))

        # Parse percentile latencies
        percentiles = {}
        for match in re.finditer(r'\s+(\d+)%\s+(\d+)', output):
            percentiles[f'p{match.group(1)}'] = int(match.group(2))

        metrics['percentiles_ms'] = percentiles
        metrics['status'] = 'ok'
        return metrics

    except FileNotFoundError:
        return {'status': 'error', 'error': 'ab (Apache Bench) not installed'}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Test timed out'}


if __name__ == "__main__":
    print("Apache Bench Testing — Usage Examples")
    print("""
    result = run_ab_test('http://localhost:8080/', requests_count=500, concurrency=20)
    print(f"  RPS: {result.get('rps')}")
    print(f"  Failed: {result.get('failed_requests')}")
    print(f"  Percentiles: {result.get('percentiles_ms')}")
    """)
