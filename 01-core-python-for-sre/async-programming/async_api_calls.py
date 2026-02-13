"""
async_api_calls.py

Concurrent API calls using asyncio for high-throughput operations.

Interview Topics:
- When to use async vs threading vs multiprocessing?
- How does asyncio event loop work?
- Difference between concurrency and parallelism?

Production Use Cases:
- Checking health of 100+ services simultaneously
- Fetching data from multiple APIs concurrently
- Parallel cloud resource discovery across regions
- Concurrent log collection from multiple pods

Prerequisites:
- aiohttp (pip install aiohttp)
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_url(
    url: str,
    timeout: float = 10.0,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Fetch a single URL asynchronously using aiohttp.

    This function is a coroutine — it can be paused while waiting for I/O,
    allowing other coroutines to run in the meantime.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        headers: Optional HTTP headers

    Returns:
        Dictionary with url, status, response_time, and data or error

    Interview Question:
        Q: How does async/await differ from threading for I/O-bound tasks?
        A: Async uses a single thread with cooperative multitasking — coroutines
           voluntarily yield control at await points. Threading uses OS-level
           threads with preemptive scheduling. Async is lighter (no thread overhead),
           avoids race conditions, and scales better for many concurrent I/O ops.
           Threading is better when you need to call blocking (non-async) libraries.
    """
    try:
        import aiohttp

        start_time = time.time()

        # Create a timeout object for the entire request
        request_timeout = aiohttp.ClientTimeout(total=timeout)

        # aiohttp.ClientSession should be reused in production,
        # but for clarity we create one per call here
        async with aiohttp.ClientSession(timeout=request_timeout) as session:
            async with session.get(url, headers=headers or {}) as response:
                # Read response body
                body = await response.text()
                elapsed = time.time() - start_time

                return {
                    'url': url,
                    'status': response.status,
                    'response_time': round(elapsed, 3),
                    'content_length': len(body),
                    'success': 200 <= response.status < 300
                }

    except ImportError:
        # Fallback if aiohttp is not installed — simulate the call
        logger.warning("aiohttp not installed. Using simulation.")
        await asyncio.sleep(0.1)  # Simulate network delay
        return {
            'url': url,
            'status': 200,
            'response_time': 0.1,
            'content_length': 0,
            'success': True,
            'simulated': True
        }
    except asyncio.TimeoutError:
        return {
            'url': url,
            'status': 0,
            'response_time': timeout,
            'error': 'Timeout',
            'success': False
        }
    except Exception as e:
        return {
            'url': url,
            'status': 0,
            'response_time': 0,
            'error': str(e),
            'success': False
        }


async def fetch_all_urls(
    urls: List[str],
    max_concurrent: int = 10,
    timeout: float = 10.0
) -> List[Dict[str, Any]]:
    """
    Fetch multiple URLs concurrently with a concurrency limit.

    Uses asyncio.Semaphore to limit the number of simultaneous requests,
    preventing resource exhaustion and API rate limiting.

    Args:
        urls: List of URLs to fetch
        max_concurrent: Maximum number of simultaneous requests
        timeout: Per-request timeout in seconds

    Returns:
        List of result dictionaries from fetch_url

    Interview Question:
        Q: How do you prevent overloading a service with too many concurrent requests?
        A: Use a semaphore to limit concurrency. asyncio.Semaphore acts as a
           token bucket — only N coroutines can proceed at once. Others wait
           until a slot becomes available. This protects both the client and server.
    """
    # Semaphore limits concurrent requests to avoid overwhelming servers
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _fetch_with_limit(url: str) -> Dict[str, Any]:
        """Wrap fetch_url with semaphore rate limiting."""
        async with semaphore:
            # Only max_concurrent coroutines reach this point simultaneously
            return await fetch_url(url, timeout=timeout)

    # Create all tasks — they start immediately but are gated by the semaphore
    tasks = [_fetch_with_limit(url) for url in urls]

    # asyncio.gather runs all tasks concurrently and collects results
    # return_exceptions=True prevents one failure from canceling everything
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results, converting any exceptions to error dicts
    processed = []
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            processed.append({
                'url': url,
                'status': 0,
                'error': str(result),
                'success': False
            })
        else:
            processed.append(result)

    return processed


async def check_services_health(
    services: Dict[str, str],
    timeout: float = 5.0
) -> Dict[str, Dict[str, Any]]:
    """
    Check health of multiple services concurrently.

    Takes a dictionary of service_name → health_url and checks them all
    in parallel, returning a comprehensive health report.

    Args:
        services: Dictionary mapping service names to health check URLs
        timeout: Health check timeout in seconds

    Returns:
        Dictionary mapping service names to health status

    Example:
        services = {
            'api': 'http://api:8080/health',
            'db': 'http://db:5432/health',
            'cache': 'http://redis:6379/health',
        }
        health = await check_services_health(services)

    Interview Question:
        Q: Design a health monitoring system for 200+ microservices.
        A: Use async to check all services concurrently (not sequentially).
           Categorize results (healthy/degraded/down). Set up alerting
           based on patterns (e.g., >10% services down = P1 alert).
           Cache results to avoid excessive polling.
    """
    start_time = time.time()

    # Build tasks for all services
    tasks = {}
    for name, url in services.items():
        tasks[name] = fetch_url(url, timeout=timeout)

    # Run all health checks concurrently
    results = await asyncio.gather(
        *tasks.values(),
        return_exceptions=True
    )

    # Build the health report
    health_report = {}
    for (name, _), result in zip(tasks.items(), results):
        if isinstance(result, Exception):
            health_report[name] = {
                'status': 'down',
                'error': str(result),
                'response_time': None
            }
        elif result.get('success'):
            health_report[name] = {
                'status': 'healthy',
                'response_time': result['response_time'],
                'http_status': result['status']
            }
        else:
            health_report[name] = {
                'status': 'unhealthy',
                'response_time': result.get('response_time'),
                'http_status': result.get('status'),
                'error': result.get('error')
            }

    total_time = time.time() - start_time
    logger.info(
        f"Health check complete: {len(services)} services checked "
        f"in {total_time:.2f}s"
    )

    return health_report


async def async_retry(
    coroutine_func,
    *args,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs
) -> Any:
    """
    Retry an async function with exponential backoff.

    Just like sync retry, but uses asyncio.sleep instead of time.sleep,
    so other coroutines can run during the wait.

    Args:
        coroutine_func: Async function to retry
        *args: Positional arguments
        max_retries: Maximum retry attempts
        delay: Initial delay in seconds
        backoff: Delay multiplier
        **kwargs: Keyword arguments

    Returns:
        Result of the coroutine

    Example:
        result = await async_retry(
            fetch_url, 'http://flaky-api.com/data',
            max_retries=5, delay=2.0
        )
    """
    current_delay = delay

    for attempt in range(max_retries + 1):
        try:
            return await coroutine_func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                logger.error(
                    f"Async retry exhausted for '{coroutine_func.__name__}' "
                    f"after {max_retries + 1} attempts: {e}"
                )
                raise

            logger.warning(
                f"Async retry {attempt + 1}/{max_retries + 1} for "
                f"'{coroutine_func.__name__}': {e}. "
                f"Waiting {current_delay:.1f}s..."
            )

            # Use asyncio.sleep so other tasks can run during the wait
            await asyncio.sleep(current_delay)
            current_delay *= backoff


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Async API Calls — Usage Examples")
    print("=" * 60)

    async def main():
        # ---- Example 1: Fetch multiple URLs ----
        print("\n--- Example 1: Concurrent URL Fetching ---")

        urls = [
            "https://httpbin.org/get",
            "https://httpbin.org/status/200",
            "https://httpbin.org/delay/1",
            "https://httpbin.org/status/404",
            "https://httpbin.org/status/500",
        ]

        start = time.time()
        results = await fetch_all_urls(urls, max_concurrent=5, timeout=5.0)
        elapsed = time.time() - start

        for r in results:
            status = "✓" if r.get('success') else "✗"
            print(f"  {status} {r['url']}: status={r.get('status')}, "
                  f"time={r.get('response_time', 'N/A')}s")

        print(f"\n  Total time: {elapsed:.2f}s (sequential would be ~{len(urls) * 1.0}s)")

        # ---- Example 2: Service health check ----
        print("\n--- Example 2: Service Health Checks ---")

        services = {
            'httpbin': 'https://httpbin.org/get',
            'github-api': 'https://api.github.com',
            'nonexistent': 'http://does-not-exist.example.com',
        }

        health = await check_services_health(services, timeout=5.0)
        for name, status in health.items():
            icon = "✓" if status['status'] == 'healthy' else "✗"
            print(f"  {icon} {name}: {status['status']}")

    # Run the async main function
    asyncio.run(main())
