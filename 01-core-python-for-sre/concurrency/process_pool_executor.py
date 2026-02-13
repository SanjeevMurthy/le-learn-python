"""
process_pool_executor.py

Advanced ProcessPoolExecutor patterns for production use.

Interview Topics:
- ProcessPoolExecutor vs Pool — when to use which?
- Handling worker process failures
- Memory management in multiprocessing

Production Use Cases:
- Map-reduce over large datasets
- Parallel test execution
- Batch image/artifact processing
- Parallel security scanning

Prerequisites:
- No external packages needed (stdlib only)
"""

import os
import time
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed, TimeoutError
from typing import List, Dict, Any, Callable, TypeVar, Iterator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

T = TypeVar('T')


def map_with_progress(
    func: Callable,
    items: list,
    max_workers: int = None,
    description: str = "Processing"
) -> List[Any]:
    """
    Process items in parallel with progress tracking.

    Args:
        func: Function to apply to each item
        items: Items to process
        max_workers: Number of workers
        description: Progress bar description

    Returns:
        List of results in original order
    """
    total = len(items)
    results = [None] * total  # Pre-allocate for ordered results

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(func, item): idx
            for idx, item in enumerate(items)
        }

        completed = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception as e:
                results[idx] = {'error': str(e)}

            completed += 1
            if completed % max(1, total // 10) == 0 or completed == total:
                pct = completed / total * 100
                print(f"  {description}: {completed}/{total} ({pct:.0f}%)")

    return results


def batch_process(
    func: Callable,
    items: list,
    batch_size: int = 100,
    max_workers: int = None
) -> List[Any]:
    """
    Process items in batches using a process pool.

    Useful when you have thousands of items and want to
    control memory usage by processing in smaller batches.

    Args:
        func: Function to apply to each item
        items: All items to process
        batch_size: Items per batch
        max_workers: Workers per batch

    Returns:
        All results combined

    Interview Question:
        Q: How do you manage memory when processing millions of records?
        A: 1. Use batch processing — don't load everything at once
           2. Use generators for lazy evaluation
           3. Process and discard — don't accumulate results in memory
           4. Use shared memory for large read-only data
           5. Monitor RSS memory per worker process
    """
    all_results = []
    total_batches = (len(items) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(items))
        batch = items[start_idx:end_idx]

        logger.info(
            f"Processing batch {batch_num + 1}/{total_batches} "
            f"(items {start_idx}-{end_idx - 1})"
        )

        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            batch_results = list(executor.map(func, batch))
            all_results.extend(batch_results)

    return all_results


def process_with_timeout(
    func: Callable,
    items: list,
    per_item_timeout: float = 30.0,
    max_workers: int = None
) -> List[Dict[str, Any]]:
    """
    Process items with per-item timeout.

    Prevents a single slow item from blocking the entire pipeline.

    Args:
        func: Function to apply
        items: Items to process
        per_item_timeout: Timeout per item in seconds
        max_workers: Number of workers

    Returns:
        Results with status and timing
    """
    results = []

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_item = {
            executor.submit(func, item): item
            for item in items
        }

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result(timeout=per_item_timeout)
                results.append({
                    'item': str(item)[:50],
                    'status': 'success',
                    'result': result
                })
            except TimeoutError:
                results.append({
                    'item': str(item)[:50],
                    'status': 'timeout',
                    'error': f'Exceeded {per_item_timeout}s timeout'
                })
                future.cancel()
            except Exception as e:
                results.append({
                    'item': str(item)[:50],
                    'status': 'error',
                    'error': str(e)
                })

    return results


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    import multiprocessing as mp

    print("=" * 60)
    print("ProcessPoolExecutor Patterns — Usage Examples")
    print("=" * 60)

    def square(n: int) -> int:
        """Simple CPU-bound computation."""
        time.sleep(0.01)
        return n * n

    # ---- Example 1: Map with progress ----
    print("\n--- Example 1: Map with Progress ---")
    numbers = list(range(20))
    results = map_with_progress(
        square, numbers,
        max_workers=min(4, mp.cpu_count()),
        description="Computing squares"
    )
    print(f"  First 10 results: {results[:10]}")

    # ---- Example 2: Batch processing ----
    print("\n--- Example 2: Batch Processing ---")
    large_list = list(range(50))
    batch_results = batch_process(
        square, large_list,
        batch_size=20,
        max_workers=2
    )
    print(f"  Processed {len(batch_results)} items in batches")

    # ---- Example 3: Timeout per item ----
    print("\n--- Example 3: Per-Item Timeout ---")

    def slow_task(n: int) -> int:
        if n == 3:
            time.sleep(100)  # This one will timeout
        return n * n

    timeout_results = process_with_timeout(
        slow_task,
        [1, 2, 3, 4, 5],
        per_item_timeout=2.0,
        max_workers=3
    )
    for r in timeout_results:
        print(f"  Item {r['item']}: {r['status']}")
