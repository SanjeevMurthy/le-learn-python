"""
threading_examples.py

Thread-based concurrency for I/O-bound tasks.

Interview Topics:
- When to use threading vs multiprocessing vs asyncio?
- What is the GIL and how does it affect threading?
- Thread safety and synchronization primitives

Production Use Cases:
- Concurrent API calls to different services
- Parallel file operations (copy, move, compress)
- Background health checking while processing requests
- Multi-target deployment (deploy to N servers concurrently)

Prerequisites:
- No external packages needed (stdlib only)
"""

import time
import logging
import threading
from typing import List, Dict, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] %(message)s'
)
logger = logging.getLogger(__name__)


def run_tasks_with_threads(
    tasks: List[Callable],
    max_workers: int = 5,
    timeout: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Run multiple tasks concurrently using a thread pool.

    Uses ThreadPoolExecutor for managed thread lifecycle.
    Results are collected as they complete (not in submission order).

    Args:
        tasks: List of callable functions (no arguments)
        max_workers: Maximum concurrent threads
        timeout: Overall timeout for all tasks

    Returns:
        List of result dictionaries with status, result/error, and timing

    Interview Question:
        Q: When would you use threading vs asyncio for I/O-bound work?
        A: Threading: when calling blocking libraries (boto3, requests, database drivers)
           that don't have async versions. asyncio: when you have async-native
           libraries or need very high concurrency (1000s of connections).
           Threading has higher overhead per "task" but works with any library.
    """
    results = []
    start_time = time.time()

    # ThreadPoolExecutor manages a pool of worker threads
    # 'with' ensures proper cleanup when done
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks and get Future objects
        future_to_index = {
            executor.submit(task): i
            for i, task in enumerate(tasks)
        }

        # Collect results as they complete
        for future in as_completed(future_to_index, timeout=timeout):
            index = future_to_index[future]
            task_start = time.time()

            try:
                result = future.result()
                results.append({
                    'index': index,
                    'status': 'success',
                    'result': result,
                    'duration': round(time.time() - start_time, 3)
                })
            except Exception as e:
                results.append({
                    'index': index,
                    'status': 'error',
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'duration': round(time.time() - start_time, 3)
                })

    # Sort by original submission order
    results.sort(key=lambda r: r['index'])
    return results


def parallel_api_calls(
    urls: List[str],
    max_workers: int = 10,
    timeout: float = 30.0
) -> List[Dict[str, Any]]:
    """
    Make parallel HTTP GET requests using threads.

    Args:
        urls: List of URLs to fetch
        max_workers: Maximum concurrent requests
        timeout: Per-request timeout

    Returns:
        List of response dictionaries

    Interview Question:
        Q: What is the GIL and how does it affect threading?
        A: The Global Interpreter Lock (GIL) prevents multiple Python threads
           from executing Python bytecode simultaneously. However, the GIL
           is RELEASED during I/O operations (network calls, file reads),
           so threading works great for I/O-bound tasks. For CPU-bound work,
           use multiprocessing instead (each process has its own GIL).
    """
    def _fetch(url: str) -> Dict[str, Any]:
        """Fetch a single URL (blocking call)."""
        try:
            import requests
            start = time.time()
            resp = requests.get(url, timeout=timeout)
            elapsed = time.time() - start
            return {
                'url': url,
                'status_code': resp.status_code,
                'response_time': round(elapsed, 3),
                'success': True
            }
        except ImportError:
            # Simulate if requests not installed
            time.sleep(0.05)
            return {'url': url, 'status_code': 200, 'success': True, 'simulated': True}
        except Exception as e:
            return {'url': url, 'error': str(e), 'success': False}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_fetch, url): url for url in urls}
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    return results


def thread_safe_counter():
    """
    Demonstrate thread-safe operations with Lock.

    Without a lock, concurrent increments can produce incorrect results
    due to race conditions (threads reading/writing shared state simultaneously).

    Interview Question:
        Q: Explain race conditions and how to prevent them.
        A: A race condition occurs when two or more threads access shared data
           concurrently and at least one modifies it. Results depend on
           scheduling order (non-deterministic). Prevent with:
           1. Locks/Mutexes — exclusive access to shared data
           2. Atomic operations — single indivisible operations
           3. Thread-local storage — each thread has its own copy
           4. Immutable data — no modification possible
    """
    counter = {'value': 0}  # Shared state
    lock = threading.Lock()

    def increment_unsafe():
        """NOT thread-safe — demonstrates race condition."""
        for _ in range(10000):
            # Read-modify-write is NOT atomic
            counter['value'] += 1

    def increment_safe():
        """Thread-safe increment using a Lock."""
        for _ in range(10000):
            with lock:
                # Only one thread can be in this block at a time
                counter['value'] += 1

    return increment_safe, increment_unsafe, counter, lock


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Threading Examples — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Concurrent task execution ----
    print("\n--- Example 1: Concurrent Tasks ---")

    def simulate_api_call(service_id: int) -> str:
        """Simulates calling an API with variable latency."""
        delay = 0.1 * (service_id % 5 + 1)
        time.sleep(delay)
        return f"Service-{service_id} responded in {delay}s"

    tasks = [lambda sid=i: simulate_api_call(sid) for i in range(8)]

    start = time.time()
    results = run_tasks_with_threads(tasks, max_workers=4)
    elapsed = time.time() - start

    for r in results:
        status = "✓" if r['status'] == 'success' else "✗"
        print(f"  {status} Task {r['index']}: {r.get('result', r.get('error'))}")
    print(f"  Total: {elapsed:.2f}s (sequential would be ~{sum(0.1 * (i % 5 + 1) for i in range(8)):.2f}s)")

    # ---- Example 2: Thread-safe counter ----
    print("\n--- Example 2: Thread Safety ---")
    safe_func, unsafe_func, counter, lock = thread_safe_counter()

    # Run safe version
    counter['value'] = 0
    threads = [threading.Thread(target=safe_func) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"  Safe counter (4 threads × 10000): {counter['value']} (expected: 40000)")

    # Run unsafe version to show the problem
    counter['value'] = 0
    threads = [threading.Thread(target=unsafe_func) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(f"  Unsafe counter (4 threads × 10000): {counter['value']} (expected: 40000, "
          f"actual may be less due to race condition)")
