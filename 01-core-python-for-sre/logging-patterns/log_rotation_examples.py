"""
log_rotation_examples.py

Log file rotation and management patterns.

Interview Topics:
- Why rotate logs? (disk space, performance, compliance)
- Rotation strategies (size-based, time-based, hybrid)
- How to avoid losing log data during rotation

Production Use Cases:
- Preventing disk full incidents from unmanaged logs
- Compliance requirements for log retention periods
- Integration with log shipping tools

Prerequisites:
- No external packages needed (stdlib only)
"""

import os
import gzip
import shutil
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def setup_size_based_rotation(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    Set up size-based log rotation.

    Creates log files that rotate when they reach max_bytes.
    Keeps up to backup_count old files (app.log.1, app.log.2, ...).

    Args:
        log_file: Path to the log file
        max_bytes: Maximum file size before rotation (bytes)
        backup_count: Number of rotated files to keep
        log_level: Logging level

    Returns:
        Configured logger

    Interview Question:
        Q: How do you prevent disk space issues from application logs?
        A: 1. Size-based rotation (rotate when file reaches N MB)
           2. Time-based rotation (daily/hourly)
           3. Set backup count to limit total files
           4. Compress rotated files
           5. Ship to central logging and set local retention
           6. Monitor disk usage with alerts at 80%
    """
    rot_logger = logging.getLogger(f"rotation.size.{os.path.basename(log_file)}")
    rot_logger.setLevel(log_level)
    rot_logger.handlers = []

    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    rot_logger.addHandler(handler)

    logger.info(
        f"Size-based rotation configured: {log_file} "
        f"(max {max_bytes // (1024 * 1024)}MB, keep {backup_count} backups)"
    )
    return rot_logger


def setup_time_based_rotation(
    log_file: str,
    when: str = 'midnight',
    interval: int = 1,
    backup_count: int = 30,
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    Set up time-based log rotation.

    Args:
        log_file: Path to the log file
        when: Rotation interval type:
              'S' = seconds, 'M' = minutes, 'H' = hours,
              'D' = days, 'midnight' = at midnight
        interval: Rotation interval count
        backup_count: Number of rotated files to keep
        log_level: Logging level

    Returns:
        Configured logger
    """
    rot_logger = logging.getLogger(f"rotation.time.{os.path.basename(log_file)}")
    rot_logger.setLevel(log_level)
    rot_logger.handlers = []

    handler = TimedRotatingFileHandler(
        log_file,
        when=when,
        interval=interval,
        backupCount=backup_count
    )
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    rot_logger.addHandler(handler)

    logger.info(
        f"Time-based rotation configured: {log_file} "
        f"(every {interval} {when}, keep {backup_count} backups)"
    )
    return rot_logger


def compress_log_file(filepath: str, remove_original: bool = True) -> Optional[str]:
    """
    Compress a log file with gzip.

    Args:
        filepath: Path to the log file
        remove_original: Whether to remove the original after compression

    Returns:
        Path to the compressed file, or None on failure
    """
    gz_path = filepath + '.gz'
    try:
        with open(filepath, 'rb') as f_in:
            with gzip.open(gz_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        original_size = os.path.getsize(filepath)
        compressed_size = os.path.getsize(gz_path)
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

        logger.info(
            f"Compressed {filepath}: {original_size} → {compressed_size} bytes "
            f"({ratio:.1f}% reduction)"
        )

        if remove_original:
            os.remove(filepath)

        return gz_path

    except Exception as e:
        logger.error(f"Failed to compress {filepath}: {e}")
        return None


def cleanup_old_logs(
    log_directory: str,
    pattern: str = "*.log*",
    max_age_days: int = 30,
    dry_run: bool = False
) -> dict:
    """
    Clean up log files older than the specified age.

    Args:
        log_directory: Directory containing log files
        pattern: Glob pattern for log files
        max_age_days: Maximum age in days
        dry_run: If True, only report what would be deleted

    Returns:
        Dictionary with cleanup statistics

    Interview Question:
        Q: Design a log retention policy for compliance.
        A: Define retention period per log type (app: 90 days, audit: 7 years,
           security: 1 year). Compress after 7 days. Ship to cold storage
           (S3 Glacier) after 30 days. Automate cleanup and verify with
           monitoring. Include log deletion in your SOC2/GDPR audits.
    """
    import glob
    import time as time_module

    cutoff_time = time_module.time() - (max_age_days * 86400)
    stats = {'scanned': 0, 'deleted': 0, 'bytes_freed': 0, 'errors': 0}

    search_path = os.path.join(log_directory, pattern)
    for filepath in glob.glob(search_path):
        stats['scanned'] += 1

        try:
            file_mtime = os.path.getmtime(filepath)
            if file_mtime < cutoff_time:
                file_size = os.path.getsize(filepath)
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete: {filepath} ({file_size} bytes)")
                else:
                    os.remove(filepath)
                    logger.info(f"Deleted: {filepath} ({file_size} bytes)")
                stats['deleted'] += 1
                stats['bytes_freed'] += file_size
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            stats['errors'] += 1

    return stats


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    import tempfile

    print("=" * 60)
    print("Log Rotation — Usage Examples")
    print("=" * 60)

    tmpdir = tempfile.mkdtemp()

    # ---- Example 1: Size-based rotation ----
    print("\n--- Example 1: Size-Based Rotation ---")
    size_logger = setup_size_based_rotation(
        os.path.join(tmpdir, "app.log"),
        max_bytes=1024,  # 1 KB for demo
        backup_count=3
    )

    # Write enough entries to trigger rotation
    for i in range(50):
        size_logger.info(f"Log entry {i + 1}: processing request with correlation id xyz-{i:03d}")

    # Check rotated files
    log_files = [f for f in os.listdir(tmpdir) if f.startswith("app.log")]
    print(f"  Created files: {sorted(log_files)}")

    # ---- Example 2: Compression ----
    print("\n--- Example 2: Log Compression ---")
    test_log = os.path.join(tmpdir, "test-compress.log")
    with open(test_log, 'w') as f:
        for i in range(100):
            f.write(f"2024-01-15 10:00:{i:02d} INFO  Processing item {i}\n")

    compressed = compress_log_file(test_log)
    if compressed:
        print(f"  Compressed to: {os.path.basename(compressed)}")

    # Cleanup
    shutil.rmtree(tmpdir)
