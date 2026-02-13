"""
cpu_profiling.py

CPU profiling techniques for Python applications.

Interview Topics:
- cProfile, py-spy, perf
- Flame graphs and call graphs
- Hot-path optimization

Prerequisites:
- cProfile (stdlib), pstats (stdlib)
"""

import cProfile
import pstats
import io
import time
import logging
from typing import Dict, Any, Callable, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def profile_function(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile a function's CPU usage.

    Interview Question:
        Q: How do you identify CPU bottlenecks in Python?
        A: 1. cProfile: built-in, function-level timing
           2. py-spy: sampling profiler, no code changes, flame graphs
           3. line_profiler: line-by-line timing (@profile decorator)
           4. perf: Linux system-level, includes C extensions
           Workflow: cProfile → find hot function → line_profiler
           for that function → optimize → re-measure.
           Common Python bottlenecks: string concatenation in loops,
           list comprehension vs generator, GIL contention.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

    return {
        'result': result,
        'total_calls': stats.total_calls,
        'total_time': stats.total_tt,
        'profile_output': stream.getvalue(),
    }


def benchmark(func: Callable, iterations: int = 100, *args, **kwargs) -> Dict[str, Any]:
    """Run a function multiple times and collect timing stats."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)

    times.sort()
    return {
        'iterations': iterations,
        'min_ms': round(times[0], 3),
        'max_ms': round(times[-1], 3),
        'avg_ms': round(sum(times) / len(times), 3),
        'p50_ms': round(times[len(times) // 2], 3),
        'p95_ms': round(times[int(len(times) * 0.95)], 3),
        'p99_ms': round(times[int(len(times) * 0.99)], 3),
    }


def find_slow_functions(profile_output: str, threshold_ms: float = 10.0) -> List[str]:
    """Parse profiling output to find slow functions."""
    slow = []
    for line in profile_output.strip().split('\n'):
        parts = line.strip().split()
        if len(parts) >= 6 and parts[0].replace('.', '').isdigit():
            try:
                cumtime = float(parts[3]) * 1000  # Convert to ms
                if cumtime > threshold_ms:
                    func_name = ' '.join(parts[5:])
                    slow.append(f"{func_name}: {cumtime:.1f}ms")
            except (ValueError, IndexError):
                continue
    return slow


if __name__ == "__main__":
    # Example: profile a simple function
    def example_work():
        return sum(i * i for i in range(10000))

    result = profile_function(example_work)
    print(f"Total calls: {result['total_calls']}, Time: {result['total_time']:.4f}s")

    stats = benchmark(example_work, iterations=50)
    print(f"Benchmark: avg={stats['avg_ms']}ms, p99={stats['p99_ms']}ms")
