"""
disk_space_cleanup.py

Automated disk space investigation and cleanup.

Prerequisites:
- psutil (pip install psutil)
"""

import os
import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_disk_usage() -> List[Dict[str, Any]]:
    """
    Get disk usage for all mounted partitions.

    Interview Question:
        Q: What causes disk space issues in production?
        A: Common culprits:
           1. Log files growing unbounded (no rotation)
           2. Docker images/layers (/var/lib/docker)
           3. /tmp files not cleaned up
           4. Core dumps from crashes
           5. Database WAL files / binlogs
           Prevention: log rotation (logrotate), disk alerts at 80%,
           Docker prune crons, tmpwatch, quotas.
    """
    import psutil

    partitions = psutil.disk_partitions()
    usage = []
    for part in partitions:
        try:
            u = psutil.disk_usage(part.mountpoint)
            usage.append({
                'mountpoint': part.mountpoint,
                'device': part.device,
                'total_gb': round(u.total / (1024 ** 3), 2),
                'used_gb': round(u.used / (1024 ** 3), 2),
                'free_gb': round(u.free / (1024 ** 3), 2),
                'percent': u.percent,
                'critical': u.percent > 90,
            })
        except PermissionError:
            continue
    return usage


def find_large_files(
    path: str = '/',
    min_size_mb: int = 100,
    max_results: int = 20
) -> List[Dict[str, Any]]:
    """Find large files in a directory tree."""
    large_files = []
    min_bytes = min_size_mb * 1024 * 1024

    for dirpath, dirnames, filenames in os.walk(path):
        # Skip special filesystems
        if any(dirpath.startswith(s) for s in ['/proc', '/sys', '/dev']):
            continue
        for f in filenames:
            try:
                full_path = os.path.join(dirpath, f)
                size = os.path.getsize(full_path)
                if size >= min_bytes:
                    large_files.append({
                        'path': full_path,
                        'size_mb': round(size / (1024 * 1024), 1),
                    })
            except (PermissionError, OSError):
                continue

        if len(large_files) >= max_results * 2:
            break

    large_files.sort(key=lambda x: x['size_mb'], reverse=True)
    return large_files[:max_results]


def find_old_log_files(
    log_dirs: List[str] = None, days: int = 30
) -> List[Dict[str, Any]]:
    """Find old log files that can be cleaned up."""
    import time

    if log_dirs is None:
        log_dirs = ['/var/log']

    cutoff = time.time() - (days * 86400)
    old_logs = []

    for log_dir in log_dirs:
        if not os.path.exists(log_dir):
            continue
        for f in os.listdir(log_dir):
            full_path = os.path.join(log_dir, f)
            try:
                if os.path.isfile(full_path) and os.path.getmtime(full_path) < cutoff:
                    old_logs.append({
                        'path': full_path,
                        'size_mb': round(os.path.getsize(full_path) / (1024 * 1024), 1),
                        'age_days': int((time.time() - os.path.getmtime(full_path)) / 86400),
                    })
            except (PermissionError, OSError):
                continue

    return sorted(old_logs, key=lambda x: x['size_mb'], reverse=True)


if __name__ == "__main__":
    print("Disk Space Cleanup")
    for d in get_disk_usage():
        status = "🔴" if d['critical'] else "🟢"
        print(f"  {status} {d['mountpoint']}: {d['used_gb']}/{d['total_gb']} GB ({d['percent']}%)")
