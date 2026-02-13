"""
io_profiling.py

I/O profiling for disk and network operations.

Prerequisites:
- psutil (pip install psutil)
"""

import time
import os
import logging
from typing import Dict, Any, Callable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def profile_io(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile I/O operations of a function.

    Interview Question:
        Q: How do you identify I/O bottlenecks?
        A: Symptoms: high iowait CPU, slow response under load.
           Tools: `iostat` (disk IOPS, latency), `iotop` (per-process),
           `strace -e trace=read,write` (syscall tracing).
           Python: asyncio for concurrent I/O, connection pooling,
           batch operations, buffered I/O.
           Database: slow queries, missing indexes, N+1 queries.
           Network: latency, connection overhead, payload size.
    """
    import psutil

    proc = psutil.Process(os.getpid())
    io_before = proc.io_counters()
    start = time.perf_counter()

    result = func(*args, **kwargs)

    elapsed = time.perf_counter() - start
    io_after = proc.io_counters()

    return {
        'result': result,
        'elapsed_ms': round(elapsed * 1000, 2),
        'read_bytes': io_after.read_bytes - io_before.read_bytes,
        'write_bytes': io_after.write_bytes - io_before.write_bytes,
        'read_count': io_after.read_count - io_before.read_count,
        'write_count': io_after.write_count - io_before.write_count,
    }


def get_disk_io_stats() -> Dict[str, Any]:
    """Get system-wide disk I/O statistics."""
    import psutil

    counters = psutil.disk_io_counters()
    if not counters:
        return {}

    return {
        'read_bytes_mb': round(counters.read_bytes / (1024 * 1024), 2),
        'write_bytes_mb': round(counters.write_bytes / (1024 * 1024), 2),
        'read_count': counters.read_count,
        'write_count': counters.write_count,
        'read_time_ms': counters.read_time,
        'write_time_ms': counters.write_time,
    }


def benchmark_file_io(
    file_size_mb: int = 10, block_size_kb: int = 4
) -> Dict[str, Any]:
    """Benchmark sequential file I/O."""
    import tempfile

    data = b'x' * (block_size_kb * 1024)
    blocks = (file_size_mb * 1024) // block_size_kb

    # Write benchmark
    with tempfile.NamedTemporaryFile(delete=False) as f:
        tmp_path = f.name
        start = time.perf_counter()
        for _ in range(blocks):
            f.write(data)
        f.flush()
        os.fsync(f.fileno())
    write_time = time.perf_counter() - start

    # Read benchmark
    start = time.perf_counter()
    with open(tmp_path, 'rb') as f:
        while f.read(block_size_kb * 1024):
            pass
    read_time = time.perf_counter() - start

    os.unlink(tmp_path)

    return {
        'file_size_mb': file_size_mb,
        'write_mbps': round(file_size_mb / write_time, 2),
        'read_mbps': round(file_size_mb / read_time, 2),
    }


if __name__ == "__main__":
    stats = get_disk_io_stats()
    print(f"Disk I/O: Read={stats.get('read_bytes_mb', 0)}MB, Write={stats.get('write_bytes_mb', 0)}MB")

    bench = benchmark_file_io(file_size_mb=5)
    print(f"File I/O: Write={bench['write_mbps']}MB/s, Read={bench['read_mbps']}MB/s")
