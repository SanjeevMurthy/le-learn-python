"""
memory_leak_detection.py

Memory leak detection and investigation.

Prerequisites:
- psutil (pip install psutil)
"""

import logging
import time
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_memory_usage() -> Dict[str, Any]:
    """
    Get system memory usage.

    Interview Question:
        Q: How do you detect and debug memory leaks in Python?
        A: Detection: monitor RSS over time (growing = leak).
           Tools: tracemalloc (stdlib), objgraph, memory_profiler.
           Common causes:
           1. Growing caches without eviction
           2. Circular references preventing GC
           3. Global state / module-level lists
           4. Closures capturing large objects
           5. C-extension memory not tracked by Python GC
           Production: monitor with Prometheus process_resident_memory_bytes.
    """
    import psutil

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        'total_gb': round(mem.total / (1024 ** 3), 2),
        'used_gb': round(mem.used / (1024 ** 3), 2),
        'available_gb': round(mem.available / (1024 ** 3), 2),
        'percent': mem.percent,
        'swap_percent': swap.percent,
    }


def get_top_memory_processes(n: int = 10) -> List[Dict[str, Any]]:
    """Get top N processes by memory usage."""
    import psutil

    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'memory_info']):
        try:
            info = proc.info
            info['rss_mb'] = round(info['memory_info'].rss / (1024 * 1024), 1)
            del info['memory_info']
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda p: p.get('memory_percent', 0), reverse=True)
    return procs[:n]


def monitor_memory_trend(pid: int, samples: int = 5, interval: float = 2.0) -> Dict[str, Any]:
    """Monitor a process's memory over time to detect leaks."""
    import psutil

    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        return {'error': f'Process {pid} not found'}

    readings = []
    for _ in range(samples):
        mem = proc.memory_info()
        readings.append(round(mem.rss / (1024 * 1024), 1))
        time.sleep(interval)

    growth = readings[-1] - readings[0]
    return {
        'pid': pid,
        'name': proc.name(),
        'readings_mb': readings,
        'growth_mb': round(growth, 1),
        'possible_leak': growth > 10,  # >10MB growth during monitoring
    }


if __name__ == "__main__":
    print("Memory Leak Detection")
    mem = get_memory_usage()
    print(f"  System: {mem['used_gb']}/{mem['total_gb']} GB ({mem['percent']}%)")

    for p in get_top_memory_processes(5):
        print(f"    PID {p['pid']} ({p['name']}): {p['rss_mb']} MB")
