"""
high_cpu_investigation.py

Automated high CPU investigation runbook.

Prerequisites:
- psutil (pip install psutil)
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_cpu_usage(interval: float = 1.0) -> Dict[str, Any]:
    """
    Get overall and per-core CPU usage.

    Interview Question:
        Q: How do you investigate high CPU usage in production?
        A: 1. `top`/`htop`: identify the process
           2. user vs system CPU: user = app code, system = kernel/IO
           3. Check recent deployments (correlation)
           4. Profile: `perf top`, `py-spy` (Python), `async-profiler` (Java)
           5. Check for: runaway loops, regex backtracking, excessive GC
           6. Short-term: kill/restart, scale out
           7. Long-term: profiling + code fix
    """
    import psutil

    overall = psutil.cpu_percent(interval=interval)
    per_core = psutil.cpu_percent(interval=0.1, percpu=True)
    times = psutil.cpu_times_percent(interval=0.1)

    return {
        'overall_percent': overall,
        'core_count': len(per_core),
        'per_core': per_core,
        'user': times.user,
        'system': times.system,
        'iowait': getattr(times, 'iowait', 0),
    }


def get_top_processes(n: int = 10) -> List[Dict[str, Any]]:
    """Get top N processes by CPU usage."""
    import psutil

    procs = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
        try:
            info = proc.info
            info['cpu_percent'] = proc.cpu_percent(interval=0.1)
            procs.append(info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    procs.sort(key=lambda p: p.get('cpu_percent', 0), reverse=True)
    return procs[:n]


def diagnose_high_cpu(threshold: float = 80.0) -> Dict[str, Any]:
    """Full CPU diagnostic."""
    cpu = get_cpu_usage()
    top_procs = get_top_processes(5)

    diagnosis = {
        'cpu': cpu,
        'top_processes': top_procs,
        'is_high': cpu['overall_percent'] > threshold,
        'recommendation': '',
    }

    if cpu['overall_percent'] > threshold:
        if cpu['iowait'] > 30:
            diagnosis['recommendation'] = 'High iowait — check disk I/O'
        elif cpu['system'] > cpu['user']:
            diagnosis['recommendation'] = 'High system CPU — check kernel/IO operations'
        else:
            diagnosis['recommendation'] = f"High user CPU — investigate PID {top_procs[0]['pid']} ({top_procs[0]['name']})"

    return diagnosis


if __name__ == "__main__":
    print("High CPU Investigation")
    result = diagnose_high_cpu()
    print(f"  CPU: {result['cpu']['overall_percent']}%")
    print(f"  High: {result['is_high']}")
    if result['recommendation']:
        print(f"  Recommendation: {result['recommendation']}")
    for p in result['top_processes'][:3]:
        print(f"    PID {p['pid']} ({p['name']}): {p['cpu_percent']}% CPU")
