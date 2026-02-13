"""
progress_bars.py

Terminal progress bar utilities.

Prerequisites:
- Standard library
"""

import sys
import time
import logging
from typing import Iterable, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def progress_bar(
    iterable: Iterable,
    total: int = 0,
    prefix: str = 'Progress',
    width: int = 40
) -> Iterable:
    """
    Simple terminal progress bar.

    Interview Question:
        Q: How do you provide feedback for long-running CLI operations?
        A: 1. Progress bars for known-length tasks
           2. Spinners for unknown-length tasks
           3. Log output with timestamps for background jobs
           4. ETA calculation for predictable tasks
           Key: never leave users wondering if the script is stuck.
    """
    total = total or len(iterable) if hasattr(iterable, '__len__') else 0

    for i, item in enumerate(iterable, 1):
        yield item
        if total:
            pct = i / total
            filled = int(width * pct)
            bar = '█' * filled + '░' * (width - filled)
            sys.stdout.write(f'\r  {prefix} |{bar}| {pct:.0%} ({i}/{total})')
            sys.stdout.flush()

    if total:
        sys.stdout.write('\n')


def spinner(message: str = 'Working'):
    """Simple spinner context manager."""
    import threading

    class Spinner:
        def __init__(self):
            self._running = False
            self._thread = None

        def __enter__(self):
            self._running = True
            self._thread = threading.Thread(target=self._spin)
            self._thread.daemon = True
            self._thread.start()
            return self

        def __exit__(self, *args):
            self._running = False
            self._thread.join()
            sys.stdout.write(f'\r  {message}... done\n')

        def _spin(self):
            chars = '⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
            i = 0
            while self._running:
                sys.stdout.write(f'\r  {message} {chars[i % len(chars)]}')
                sys.stdout.flush()
                time.sleep(0.1)
                i += 1

    return Spinner()


if __name__ == "__main__":
    # Progress bar demo
    items = list(range(20))
    for item in progress_bar(items, prefix='Processing'):
        time.sleep(0.05)

    # Spinner demo
    with spinner('Loading config'):
        time.sleep(1)
