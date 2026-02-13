"""
health_check_automation.py

Health check endpoint testing and monitoring.

Prerequisites:
- requests (pip install requests)
"""

import time
import logging
from typing import Dict, Any, List, Callable
from concurrent.futures import ThreadPoolExecutor

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def http_health_check(
    url: str, timeout: int = 5, expected_status: int = 200
) -> Dict[str, Any]:
    """
    Perform an HTTP health check.

    Interview Question:
        Q: What makes a good health check endpoint?
        A: Liveness: is the process alive? (simple 200 OK)
           Readiness: can it serve traffic? (check dependencies)
           Startup: has it finished initializing? (K8s startup probe)
           Best practices:
           - Liveness: lightweight, no dependency checks (avoid cascading)
           - Readiness: check DB connection, cache, required services
           - Include response time in health check response
           - Never cache health check responses
    """
    start = time.perf_counter()
    try:
        response = requests.get(url, timeout=timeout)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        return {
            'url': url,
            'healthy': response.status_code == expected_status,
            'status_code': response.status_code,
            'response_time_ms': elapsed_ms,
        }
    except requests.RequestException as e:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            'url': url,
            'healthy': False,
            'error': str(e),
            'response_time_ms': elapsed_ms,
        }


def check_all_services(
    services: List[Dict[str, str]], max_workers: int = 10
) -> List[Dict[str, Any]]:
    """Check health of multiple services concurrently."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(http_health_check, s['url']): s
            for s in services
        }
        for future in futures:
            service = futures[future]
            result = future.result()
            result['service'] = service.get('name', result['url'])
            results.append(result)

    return results


if __name__ == "__main__":
    services = [
        {'name': 'Google', 'url': 'https://www.google.com'},
        {'name': 'GitHub', 'url': 'https://github.com'},
    ]
    for r in check_all_services(services):
        status = "✅" if r['healthy'] else "❌"
        print(f"  {status} {r['service']}: {r['response_time_ms']}ms")
