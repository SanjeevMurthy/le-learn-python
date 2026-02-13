"""
concurrent_health_checks.py

Parallel health checks for multiple services using asyncio.

Interview Topics:
- How to check 100+ services quickly?
- asyncio.gather vs asyncio.wait
- Timeout handling in concurrent operations

Production Use Cases:
- Monitoring dashboard backend
- Pre-deployment verification of dependencies
- Periodic service mesh health validation
- Multi-region endpoint checking

Prerequisites:
- aiohttp (pip install aiohttp) — optional, falls back to simulation
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a single health check."""
    service_name: str
    url: str
    is_healthy: bool
    response_time_ms: float = 0.0
    status_code: int = 0
    error: Optional[str] = None


async def check_single_service(
    service_name: str,
    url: str,
    timeout: float = 5.0,
    expected_status: int = 200
) -> HealthCheckResult:
    """
    Check health of a single service endpoint.

    Args:
        service_name: Human-readable service name
        url: Health check URL
        timeout: Request timeout in seconds
        expected_status: Expected HTTP status code

    Returns:
        HealthCheckResult with timing and status info
    """
    start = time.time()
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                elapsed_ms = (time.time() - start) * 1000
                return HealthCheckResult(
                    service_name=service_name,
                    url=url,
                    is_healthy=(resp.status == expected_status),
                    response_time_ms=round(elapsed_ms, 2),
                    status_code=resp.status
                )
    except ImportError:
        # Simulate health check when aiohttp isn't installed
        await asyncio.sleep(0.05)
        elapsed_ms = (time.time() - start) * 1000
        return HealthCheckResult(
            service_name=service_name,
            url=url,
            is_healthy=True,
            response_time_ms=round(elapsed_ms, 2),
            status_code=200
        )
    except asyncio.TimeoutError:
        elapsed_ms = (time.time() - start) * 1000
        return HealthCheckResult(
            service_name=service_name,
            url=url,
            is_healthy=False,
            response_time_ms=round(elapsed_ms, 2),
            error=f"Timeout after {timeout}s"
        )
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return HealthCheckResult(
            service_name=service_name,
            url=url,
            is_healthy=False,
            response_time_ms=round(elapsed_ms, 2),
            error=str(e)
        )


async def check_all_services(
    services: Dict[str, str],
    timeout: float = 5.0,
    max_concurrent: int = 20
) -> List[HealthCheckResult]:
    """
    Check health of all services concurrently with concurrency limit.

    Args:
        services: Dict of service_name → health_url
        timeout: Per-request timeout
        max_concurrent: Maximum simultaneous checks

    Returns:
        List of HealthCheckResult for all services

    Interview Question:
        Q: How would you design a health check system for 500+ microservices?
        A: Use async I/O for concurrency, semaphore for rate limiting,
           configurable timeouts per service, categorize results
           (healthy/degraded/down), cache results with TTL, alert on
           patterns (>5% down = P1).
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _limited_check(name: str, url: str) -> HealthCheckResult:
        async with semaphore:
            return await check_single_service(name, url, timeout)

    tasks = [_limited_check(name, url) for name, url in services.items()]
    results = await asyncio.gather(*tasks)
    return list(results)


def generate_health_report(results: List[HealthCheckResult]) -> Dict[str, Any]:
    """
    Generate a summary report from health check results.

    Args:
        results: List of HealthCheckResult

    Returns:
        Summary report with counts, slowest services, etc.
    """
    healthy = [r for r in results if r.is_healthy]
    unhealthy = [r for r in results if not r.is_healthy]

    # Sort by response time to find slowest services
    by_response_time = sorted(results, key=lambda r: r.response_time_ms, reverse=True)

    avg_response = (
        sum(r.response_time_ms for r in results) / len(results) if results else 0
    )

    return {
        'total': len(results),
        'healthy': len(healthy),
        'unhealthy': len(unhealthy),
        'health_percentage': round(len(healthy) / len(results) * 100, 1) if results else 0,
        'avg_response_ms': round(avg_response, 2),
        'slowest_services': [
            {'name': r.service_name, 'time_ms': r.response_time_ms}
            for r in by_response_time[:5]
        ],
        'failed_services': [
            {'name': r.service_name, 'error': r.error}
            for r in unhealthy
        ]
    }


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Concurrent Health Checks — Usage Examples")
    print("=" * 60)

    async def main():
        # Define services to check
        services = {
            'httpbin': 'https://httpbin.org/get',
            'github-api': 'https://api.github.com',
            'google': 'https://www.google.com',
            'nonexistent': 'http://this-does-not-exist.example.com',
        }

        print(f"\nChecking {len(services)} services concurrently...")
        start = time.time()

        results = await check_all_services(services, timeout=5.0)
        elapsed = time.time() - start

        # Print individual results
        for r in results:
            icon = "✓" if r.is_healthy else "✗"
            print(f"  {icon} {r.service_name}: "
                  f"{'healthy' if r.is_healthy else r.error} "
                  f"({r.response_time_ms:.0f}ms)")

        # Generate and print report
        report = generate_health_report(results)
        print(f"\n  Summary: {report['healthy']}/{report['total']} healthy "
              f"({report['health_percentage']}%)")
        print(f"  Avg response: {report['avg_response_ms']:.0f}ms")
        print(f"  Total check time: {elapsed:.2f}s")

    asyncio.run(main())
