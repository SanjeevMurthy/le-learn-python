"""
multiprocessing_examples.py

Process-based parallelism for CPU-bound tasks.

Interview Topics:
- Why multiprocessing over threading for CPU-bound work?
- Inter-process communication (IPC) patterns
- Shared memory vs message passing

Production Use Cases:
- Parsing large log files in parallel
- CPU-intensive data transformations
- Parallel image/artifact processing
- Batch operations across large datasets

Prerequisites:
- No external packages needed (stdlib only)
"""

import os
import time
import logging
import multiprocessing as mp
from typing import List, Dict, Any, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def cpu_intensive_task(data: str) -> Dict[str, Any]:
    """
    Simulate a CPU-intensive operation.

    This represents work like log parsing, data hashing,
    JSON schema validation, or report generation.

    Args:
        data: Input data to process

    Returns:
        Processing result with timing
    """
    start = time.time()

    # Simulate CPU work — compute a hash many times
    result = data
    for _ in range(100000):
        result = str(hash(result))

    elapsed = time.time() - start
    return {
        'input_length': len(data),
        'result_hash': result[:16],
        'processing_time': round(elapsed, 3),
        'pid': os.getpid()
    }


def run_with_process_pool(
    func: Callable,
    items: list,
    max_workers: int = None,
    timeout: float = None
) -> List[Dict[str, Any]]:
    """
    Run a function across multiple items using a process pool.

    Each item is processed by a separate worker process,
    bypassing the GIL for true parallelism.

    Args:
        func: Function to apply to each item
        items: List of items to process
        max_workers: Number of worker processes (default: CPU count)
        timeout: Per-task timeout

    Returns:
        List of results

    Interview Question:
        Q: When would you choose multiprocessing over threading?
        A: When the work is CPU-bound (computation, not I/O).
           Threading is limited by the GIL for CPU work — only one thread
           runs Python bytecode at a time. Multiprocessing creates separate
           processes, each with its own Python interpreter and GIL,
           achieving true parallelism on multi-core CPUs.
    """
    if max_workers is None:
        max_workers = min(len(items), mp.cpu_count())

    results = []

    # ProcessPoolExecutor creates separate OS processes
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Map each item to a future
        future_to_item = {
            executor.submit(func, item): item
            for item in items
        }

        for future in as_completed(future_to_item, timeout=timeout):
            item = future_to_item[future]
            try:
                result = future.result()
                results.append({
                    'input': str(item)[:50],
                    'status': 'success',
                    **result
                })
            except Exception as e:
                results.append({
                    'input': str(item)[:50],
                    'status': 'error',
                    'error': str(e)
                })

    return results


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """
    Split a list into chunks for parallel processing.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def parallel_file_processing(
    filepaths: List[str],
    processor_func: Callable,
    max_workers: int = None
) -> Dict[str, Any]:
    """
    Process multiple files in parallel using separate processes.

    Args:
        filepaths: List of file paths to process
        processor_func: Function that takes a filepath and returns result
        max_workers: Number of worker processes

    Returns:
        Aggregated results from all files

    Interview Question:
        Q: How do you process 1000 large files efficiently?
        A: 1. Determine if I/O-bound or CPU-bound (usually both)
           2. For I/O-heavy: use threading or asyncio
           3. For CPU-heavy parsing: use multiprocessing
           4. Combine: async I/O to read + process pool to parse
           5. Monitor memory — don't load all files at once
           6. Use chunk-based processing for very large files
    """
    if max_workers is None:
        max_workers = min(len(filepaths), mp.cpu_count())

    results = {
        'total_files': len(filepaths),
        'processed': 0,
        'errors': 0,
        'file_results': []
    }

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {
            executor.submit(processor_func, fp): fp
            for fp in filepaths
        }

        for future in as_completed(future_to_path):
            filepath = future_to_path[future]
            try:
                result = future.result()
                results['processed'] += 1
                results['file_results'].append({
                    'filepath': filepath,
                    'status': 'success',
                    'result': result
                })
            except Exception as e:
                results['errors'] += 1
                results['file_results'].append({
                    'filepath': filepath,
                    'status': 'error',
                    'error': str(e)
                })

    return results


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Multiprocessing Examples — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Process pool for CPU-bound work ----
    print("\n--- Example 1: CPU-Bound Parallel Processing ---")

    test_data = [f"data-item-{i}-{'x' * 100}" for i in range(8)]
    cpu_count = mp.cpu_count()
    print(f"  CPU cores: {cpu_count}")

    # Sequential baseline
    start = time.time()
    seq_results = [cpu_intensive_task(d) for d in test_data]
    sequential_time = time.time() - start
    print(f"  Sequential: {sequential_time:.3f}s")

    # Parallel execution
    start = time.time()
    par_results = run_with_process_pool(
        cpu_intensive_task,
        test_data,
        max_workers=min(4, cpu_count)
    )
    parallel_time = time.time() - start
    print(f"  Parallel ({min(4, cpu_count)} workers): {parallel_time:.3f}s")

    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    print(f"  Speedup: {speedup:.1f}x")

    # Show which PIDs handled the work
    pids = set(r.get('pid', 'N/A') for r in par_results)
    print(f"  Worker PIDs: {pids}")

    # ---- Example 2: Chunked processing ----
    print("\n--- Example 2: Chunked Processing ---")
    large_dataset = list(range(100))
    chunks = chunk_list(large_dataset, chunk_size=25)
    print(f"  {len(large_dataset)} items → {len(chunks)} chunks of 25")
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i}: items {chunk[0]}-{chunk[-1]}")
