"""
performance_benchmarks.py

Custom performance benchmarks for common operations.

Prerequisites:
- Standard library
"""

import time
import json
import hashlib
import logging
from typing import Dict, Any, List, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_benchmark(name: str, func: Callable, iterations: int = 10000) -> Dict[str, Any]:
    """Run a benchmark and return timing statistics."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        func()
        elapsed = time.perf_counter_ns() - start
        times.append(elapsed)

    times.sort()
    return {
        'name': name,
        'iterations': iterations,
        'avg_ns': round(sum(times) / len(times)),
        'min_ns': times[0],
        'max_ns': times[-1],
        'p50_ns': times[len(times) // 2],
        'p99_ns': times[int(len(times) * 0.99)],
    }


def benchmark_suite() -> List[Dict[str, Any]]:
    """
    Run a suite of common operation benchmarks.

    Interview Question:
        Q: What are common Python performance pitfalls?
        A: 1. String concat in loops (use join or f-strings)
           2. List.append in tight loop (pre-allocate or use generators)
           3. Global variable lookup (local is faster)
           4. Attribute access in loops (cache `obj.method`)
           5. Not using built-in C-optimized functions
           6. GIL contention in multithreaded CPU work
           7. Excessive logging in hot paths
    """
    results = []

    # Dict lookup vs list search
    data_dict = {str(i): i for i in range(1000)}
    data_list = list(range(1000))
    results.append(run_benchmark('dict_lookup', lambda: data_dict.get('500'), 10000))
    results.append(run_benchmark('list_search', lambda: 500 in data_list, 10000))

    # String concatenation
    results.append(run_benchmark('str_join', lambda: ''.join(str(i) for i in range(100)), 1000))
    results.append(run_benchmark('f_string', lambda: f"{'x' * 100}", 10000))

    # JSON serialize
    obj = {'key': 'value', 'num': 42, 'list': [1, 2, 3]}
    results.append(run_benchmark('json_dumps', lambda: json.dumps(obj), 10000))
    s = json.dumps(obj)
    results.append(run_benchmark('json_loads', lambda: json.loads(s), 10000))

    # Hashing
    data = b'benchmark data for hashing'
    results.append(run_benchmark('sha256', lambda: hashlib.sha256(data).hexdigest(), 10000))
    results.append(run_benchmark('md5', lambda: hashlib.md5(data).hexdigest(), 10000))

    return results


if __name__ == "__main__":
    print("Performance Benchmarks")
    print(f"  {'Operation':<20} {'Avg':>10} {'P50':>10} {'P99':>10}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10}")
    for r in benchmark_suite():
        print(f"  {r['name']:<20} {r['avg_ns']:>8}ns {r['p50_ns']:>8}ns {r['p99_ns']:>8}ns")
