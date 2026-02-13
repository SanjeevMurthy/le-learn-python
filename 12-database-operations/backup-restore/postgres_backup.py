"""
postgres_backup.py

PostgreSQL backup automation.

Prerequisites:
- subprocess (for pg_dump/pg_basebackup)
"""

import subprocess
import os
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def pg_dump(
    database: str,
    output_dir: str,
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres',
    format: str = 'custom'
) -> Dict[str, Any]:
    """
    Perform a PostgreSQL logical backup.

    Interview Question:
        Q: pg_dump vs pg_basebackup — when to use each?
        A: pg_dump: logical backup, single database, SQL or custom format.
           Good for: schema-only, single table, cross-version migration.
           pg_basebackup: physical backup, entire cluster, binary copy.
           Good for: PITR (with WAL archiving), replica setup.
           pg_dump: slower for large DBs but flexible.
           pg_basebackup: faster, but same PG version required.
           Production: pg_basebackup + WAL archiving for PITR,
           pg_dump for dev/staging data subsets.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    ext = {'custom': 'dump', 'plain': 'sql', 'tar': 'tar'}.get(format, 'dump')
    output_file = os.path.join(output_dir, f'{database}_{timestamp}.{ext}')

    cmd = [
        'pg_dump',
        '-h', host, '-p', str(port), '-U', user,
        '-F', format[0],  # c=custom, p=plain, t=tar
        '-f', output_file,
        database,
    ]

    env = os.environ.copy()
    # PGPASSWORD from env or .pgpass

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, env=env)
        if result.returncode == 0:
            size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            logger.info(f"Backup complete: {output_file} ({size} bytes)")
            return {'file': output_file, 'size_bytes': size, 'status': 'ok'}
        return {'status': 'error', 'error': result.stderr}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Backup timed out'}


def pg_restore(
    dump_file: str,
    database: str,
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres'
) -> Dict[str, Any]:
    """Restore a PostgreSQL backup."""
    cmd = [
        'pg_restore',
        '-h', host, '-p', str(port), '-U', user,
        '-d', database,
        '--clean', '--if-exists',
        dump_file,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode == 0:
        logger.info(f"Restore complete: {dump_file} → {database}")
        return {'status': 'ok', 'database': database}
    return {'status': 'error', 'error': result.stderr}


if __name__ == "__main__":
    print("PostgreSQL Backup — Usage Examples")
    print("""
    pg_dump('mydb', '/backups', host='db.example.com')
    pg_restore('/backups/mydb_20240115.dump', 'mydb_restore')
    """)
