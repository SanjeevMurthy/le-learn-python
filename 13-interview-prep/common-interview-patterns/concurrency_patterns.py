"""
concurrency_patterns.py

Common concurrency patterns for DevOps/SRE interviews.
"""

import threading
import time
import logging
from typing import Any, Callable, Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fan_out_fan_in(
    tasks: List[Callable],
    max_workers: int = 10
) -> List[Any]:
    """
    Fan-out work to threads, fan-in results.

    Interview Question:
        Q: Explain threading vs multiprocessing vs asyncio.
        A: Threading: I/O-bound work (API calls, file I/O). GIL limits
           CPU parallelism. Good for: HTTP requests, DB queries.
           Multiprocessing: CPU-bound work. True parallelism.
           Good for: data processing, image manipulation.
           Asyncio: I/O-bound, single-threaded cooperative multitasking.
           Good for: high-concurrency network servers, web scraping.
           Rule of thumb: I/O → asyncio or threading, CPU → multiprocessing.
    """
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(task): i for i, task in enumerate(tasks)}
        for future in as_completed(futures):
            results.append(future.result())
    return results


class ProducerConsumer:
    """Producer-consumer pattern with a bounded queue."""

    def __init__(self, queue_size: int = 100):
        self._queue: Queue = Queue(maxsize=queue_size)
        self._running = True

    def produce(self, items: List[Any]) -> None:
        for item in items:
            if not self._running:
                break
            self._queue.put(item)
        self._queue.put(None)  # Sentinel

    def consume(self, handler: Callable[[Any], None]) -> int:
        processed = 0
        while True:
            item = self._queue.get()
            if item is None:
                break
            handler(item)
            processed += 1
        return processed

    def stop(self) -> None:
        self._running = False


class ReadWriteLock:
    """
    Read-write lock: multiple readers OR one writer.

    Interview Question:
        Q: When would you use a read-write lock?
        A: When reads far outnumber writes (e.g., config cache,
           routing tables, feature flags). Multiple readers can
           access concurrently. Writer gets exclusive access.
           Trade-off: more complex than simple lock, risk of
           writer starvation if too many readers.
    """

    def __init__(self):
        self._read_lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._readers = 0

    def acquire_read(self):
        with self._read_lock:
            self._readers += 1
            if self._readers == 1:
                self._write_lock.acquire()

    def release_read(self):
        with self._read_lock:
            self._readers -= 1
            if self._readers == 0:
                self._write_lock.release()

    def acquire_write(self):
        self._write_lock.acquire()

    def release_write(self):
        self._write_lock.release()


if __name__ == "__main__":
    # Fan-out/fan-in demo
    tasks = [lambda i=i: f"result_{i}" for i in range(5)]
    results = fan_out_fan_in(tasks, max_workers=3)
    print(f"  Fan-out results: {results}")
