"""
data_migration.py

Large-scale data migration utilities.

Prerequisites:
- Standard library
"""

import time
import logging
from typing import Dict, Any, List, Callable, Iterator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def batch_migrate(
    fetch_batch: Callable[[int, int], List[Any]],
    process_batch: Callable[[List[Any]], int],
    batch_size: int = 1000,
    max_batches: int = 0,
    delay_seconds: float = 0.1
) -> Dict[str, Any]:
    """
    Migrate data in batches to avoid locking.

    Interview Question:
        Q: How do you migrate large datasets without downtime?
        A: 1. Batch processing: small chunks, throttled (avoid lock contention)
           2. Dual-write: write to old + new during migration
           3. Shadow reads: compare old vs new results
           4. Backfill: process historical data in batches
           5. Feature flag: switch reads to new source when ready
           6. Verify: row counts, checksums, sample comparison
           Key: never do a single large UPDATE/INSERT. Always batch.
    """
    total_processed = 0
    batch_num = 0
    start = time.time()

    while True:
        batch_num += 1
        if max_batches and batch_num > max_batches:
            break

        offset = (batch_num - 1) * batch_size
        batch = fetch_batch(offset, batch_size)
        if not batch:
            break

        processed = process_batch(batch)
        total_processed += processed

        if batch_num % 100 == 0:
            elapsed = time.time() - start
            rate = total_processed / elapsed if elapsed > 0 else 0
            logger.info(f"Batch {batch_num}: {total_processed} rows ({rate:.0f}/s)")

        time.sleep(delay_seconds)

    elapsed = time.time() - start
    return {
        'total_processed': total_processed,
        'batches': batch_num,
        'elapsed_seconds': round(elapsed, 2),
        'rate_per_second': round(total_processed / elapsed, 1) if elapsed > 0 else 0,
    }


def verify_migration(
    source_count_fn: Callable[[], int],
    target_count_fn: Callable[[], int],
    sample_check_fn: Callable[[], bool] = lambda: True
) -> Dict[str, Any]:
    """Verify data migration completeness and accuracy."""
    source = source_count_fn()
    target = target_count_fn()

    return {
        'source_count': source,
        'target_count': target,
        'counts_match': source == target,
        'sample_check': sample_check_fn(),
        'verified': source == target and sample_check_fn(),
    }


if __name__ == "__main__":
    print("Data Migration — Usage Examples")
    print("""
    # Batch migration example
    result = batch_migrate(
        fetch_batch=lambda offset, limit: db.query(f'SELECT * FROM old LIMIT {limit} OFFSET {offset}'),
        process_batch=lambda rows: db.insert_many('new_table', rows),
        batch_size=1000,
        delay_seconds=0.05
    )
    print(f"Migrated {result['total_processed']} rows in {result['elapsed_seconds']}s")

    # Verify
    verify = verify_migration(
        source_count_fn=lambda: db.count('old_table'),
        target_count_fn=lambda: db.count('new_table'),
    )
    print(f"Verified: {verify['verified']}")
    """)
