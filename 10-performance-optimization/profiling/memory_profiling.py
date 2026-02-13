"""
memory_profiling.py

Memory profiling and leak detection.

Prerequisites:
- tracemalloc (stdlib), psutil (pip install psutil)
"""

import tracemalloc
import sys
import logging
from typing import Dict, Any, List, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def profile_memory(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile memory allocations of a function.

    Interview Question:
        Q: How do you debug memory issues in Python?
        A: Tools hierarchy:
           1. tracemalloc (stdlib): track allocation origins
           2. sys.getsizeof(): size of individual objects
           3. objgraph: reference graphs, find leaks
           4. memory_profiler: line-by-line memory usage
           5. psutil: process-level RSS/VMS tracking
           Common leaks: growing dicts/lists (caches without eviction),
           circular references, closures capturing large objects,
           __del__ preventing garbage collection.
    """
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()

    result = func(*args, **kwargs)

    snapshot_after = tracemalloc.take_snapshot()
    tracemalloc.stop()

    # Compare snapshots
    stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    top_allocations = [
        {
            'file': str(stat.traceback),
            'size_kb': round(stat.size / 1024, 2),
            'count': stat.count,
        }
        for stat in stats[:10]
    ]

    current, peak = tracemalloc.get_traced_memory() if tracemalloc.is_tracing() else (0, 0)

    return {
        'result': result,
        'top_allocations': top_allocations,
        'total_allocated_kb': round(sum(s.size for s in stats if s.size > 0) / 1024, 2),
    }


def get_object_sizes(obj: Any, seen: set = None) -> int:
    """Recursively calculate the size of an object."""
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    if isinstance(obj, dict):
        size += sum(get_object_sizes(k, seen) + get_object_sizes(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(get_object_sizes(item, seen) for item in obj)

    return size


def check_process_memory() -> Dict[str, Any]:
    """Get current process memory usage."""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    mem = process.memory_info()

    return {
        'rss_mb': round(mem.rss / (1024 * 1024), 2),
        'vms_mb': round(mem.vms / (1024 * 1024), 2),
        'percent': round(process.memory_percent(), 2),
    }


if __name__ == "__main__":
    def example_allocator():
        return [{'key': f'item_{i}', 'data': 'x' * 100} for i in range(1000)]

    result = profile_memory(example_allocator)
    print(f"Total allocated: {result['total_allocated_kb']} KB")
    for alloc in result['top_allocations'][:3]:
        print(f"  {alloc['file']}: {alloc['size_kb']} KB ({alloc['count']} objects)")

    mem = check_process_memory()
    print(f"Process: RSS={mem['rss_mb']}MB, VMS={mem['vms_mb']}MB")
