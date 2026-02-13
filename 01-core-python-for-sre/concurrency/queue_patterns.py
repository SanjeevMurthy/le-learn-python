"""
queue_patterns.py

Producer-consumer patterns with queues for concurrent data processing.

Interview Topics:
- Producer-consumer pattern
- Thread-safe queues
- Worker pool with queue-based task distribution

Production Use Cases:
- Log processing pipeline (producer reads logs, consumers parse & store)
- Event-driven architectures
- Rate-limited API call dispatching
- Background job processing

Prerequisites:
- No external packages needed (stdlib only)
"""

import time
import logging
import queue
import threading
from typing import Any, Callable, Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(threadName)s] %(message)s'
)
logger = logging.getLogger(__name__)


def producer_consumer_basic(
    items: list,
    process_func: Callable,
    num_consumers: int = 3,
    queue_size: int = 0
) -> List[Any]:
    """
    Basic producer-consumer pattern with a shared queue.

    Producer puts items into the queue; consumers pull and process them.
    queue.Queue is thread-safe — no manual locking needed.

    Args:
        items: Items for producer to enqueue
        process_func: Function each consumer applies to items
        num_consumers: Number of consumer threads
        queue_size: Max queue size (0 = unlimited)

    Returns:
        List of processed results

    Interview Question:
        Q: Explain the producer-consumer pattern.
        A: Decouples production from consumption using a buffer (queue).
           Producer adds work items to the queue without waiting for
           processing. Consumers pull from the queue and process independently.
           Benefits: load leveling, different speeds, crash isolation.
           The queue acts as a shock absorber between fast producers
           and slow consumers.
    """
    work_queue = queue.Queue(maxsize=queue_size)
    results = []
    results_lock = threading.Lock()

    def consumer():
        """Consumer thread — pulls work from queue until poison pill."""
        while True:
            item = work_queue.get()
            if item is None:
                # None is the "poison pill" — signals consumer to stop
                work_queue.task_done()
                break

            try:
                result = process_func(item)
                with results_lock:
                    results.append(result)
            except Exception as e:
                logger.error(f"Consumer error: {e}")
            finally:
                # Signal that this item has been processed
                work_queue.task_done()

    # Start consumer threads
    consumers = []
    for i in range(num_consumers):
        t = threading.Thread(target=consumer, name=f"consumer-{i}")
        t.start()
        consumers.append(t)

    # Producer: add all items to the queue
    for item in items:
        work_queue.put(item)

    # Send poison pills — one per consumer
    for _ in range(num_consumers):
        work_queue.put(None)

    # Wait for all items to be processed
    work_queue.join()

    # Wait for all consumer threads to finish
    for t in consumers:
        t.join()

    return results


def priority_queue_processor(
    tasks: List[Dict[str, Any]],
    process_func: Callable,
    num_workers: int = 3
) -> List[Dict[str, Any]]:
    """
    Process tasks by priority using PriorityQueue.

    Higher priority tasks (lower number) are processed first.
    Useful for handling critical alerts before routine maintenance.

    Args:
        tasks: List of dicts with 'priority' (int) and 'data' fields
        process_func: Function to process each task's data
        num_workers: Number of worker threads

    Returns:
        List of results in processing order

    Interview Question:
        Q: Design a job scheduler with priority support.
        A: Use a priority queue backed by a min-heap. Jobs with lower
           priority numbers are dequeued first. Add aging to prevent
           starvation (increment priority of old jobs). Support priority
           inversion detection for dependent jobs.
    """
    pq = queue.PriorityQueue()
    results = []
    results_lock = threading.Lock()
    counter = 0  # Tie-breaker for equal priorities

    def worker():
        while True:
            try:
                priority, idx, task_data = pq.get(timeout=2.0)
                try:
                    result = process_func(task_data)
                    with results_lock:
                        results.append({
                            'priority': priority,
                            'data': task_data,
                            'result': result
                        })
                except Exception as e:
                    logger.error(f"Worker error: {e}")
                finally:
                    pq.task_done()
            except queue.Empty:
                break

    # Enqueue tasks with priority
    for task in tasks:
        pq.put((task['priority'], counter, task['data']))
        counter += 1

    # Start workers
    workers = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, name=f"worker-{i}")
        t.start()
        workers.append(t)

    # Wait for completion
    pq.join()
    for t in workers:
        t.join()

    return results


def rate_limited_queue(
    items: list,
    process_func: Callable,
    calls_per_second: float = 5.0,
    num_workers: int = 1
) -> List[Any]:
    """
    Process items through a rate-limited queue.

    Ensures we don't exceed API rate limits by controlling
    how fast items are dispatched from the queue.

    Args:
        items: Items to process
        process_func: Processing function
        calls_per_second: Maximum calls per second
        num_workers: Number of worker threads

    Returns:
        List of results

    Interview Question:
        Q: How do you handle API rate limits in automation scripts?
        A: 1. Token bucket algorithm for rate limiting
           2. Queue-based dispatching with delay between calls
           3. Read Retry-After headers from API responses
           4. Implement exponential backoff on 429 errors
           5. Distribute calls across multiple API keys/regions
    """
    work_queue = queue.Queue()
    results = []
    results_lock = threading.Lock()
    min_interval = 1.0 / calls_per_second

    def worker():
        while True:
            item = work_queue.get()
            if item is None:
                work_queue.task_done()
                break

            start = time.time()
            try:
                result = process_func(item)
                with results_lock:
                    results.append(result)
            except Exception as e:
                logger.error(f"Rate-limited worker error: {e}")
            finally:
                # Enforce rate limit by sleeping for remaining interval
                elapsed = time.time() - start
                sleep_time = max(0, min_interval - elapsed)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                work_queue.task_done()

    # Start workers
    workers = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, name=f"rl-worker-{i}")
        t.start()
        workers.append(t)

    # Enqueue items
    for item in items:
        work_queue.put(item)

    # Poison pills
    for _ in range(num_workers):
        work_queue.put(None)

    work_queue.join()
    for t in workers:
        t.join()

    return results


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Queue Patterns — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Basic producer-consumer ----
    print("\n--- Example 1: Basic Producer-Consumer ---")
    items = list(range(10))

    def double(x):
        time.sleep(0.05)
        return x * 2

    results = producer_consumer_basic(items, double, num_consumers=3)
    print(f"  Input:  {items}")
    print(f"  Output: {sorted(results)}")

    # ---- Example 2: Priority queue ----
    print("\n--- Example 2: Priority Queue ---")
    tasks = [
        {'priority': 3, 'data': 'routine-backup'},
        {'priority': 1, 'data': 'critical-alert'},
        {'priority': 2, 'data': 'deploy-hotfix'},
        {'priority': 1, 'data': 'security-patch'},
        {'priority': 3, 'data': 'log-rotation'},
    ]

    def handle_task(task_data):
        time.sleep(0.02)
        return f"Processed: {task_data}"

    pq_results = priority_queue_processor(tasks, handle_task, num_workers=2)
    print("  Processing order:")
    for r in pq_results:
        print(f"    Priority {r['priority']}: {r['data']}")

    # ---- Example 3: Rate-limited queue ----
    print("\n--- Example 3: Rate-Limited Queue ---")
    api_calls = [f"api-call-{i}" for i in range(5)]

    start = time.time()
    rl_results = rate_limited_queue(
        api_calls,
        lambda x: f"Response for {x}",
        calls_per_second=10.0,
        num_workers=1
    )
    elapsed = time.time() - start
    print(f"  Processed {len(rl_results)} calls in {elapsed:.2f}s "
          f"(rate limited to 10/s)")
