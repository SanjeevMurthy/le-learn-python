"""
mysql_backup.py

MySQL backup automation.

Prerequisites:
- subprocess (for mysqldump)
"""

import subprocess
import os
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def mysqldump(
    database: str,
    output_dir: str,
    host: str = 'localhost',
    port: int = 3306,
    user: str = 'root',
    single_transaction: bool = True,
    routines: bool = True
) -> Dict[str, Any]:
    """
    Perform a MySQL logical backup.

    Interview Question:
        Q: How do you ensure consistent MySQL backups?
        A: --single-transaction: consistent snapshot for InnoDB
           (no lock for reads). FLUSH TABLES WITH READ LOCK for MyISAM.
           --master-data=2: record binlog position for PITR.
           --routines: include stored procedures and functions.
           For large DBs: xtrabackup (hot physical backup, incremental).
           Cloud: RDS automated snapshots, Aurora continuous backup.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'{database}_{timestamp}.sql')

    cmd = [
        'mysqldump',
        '-h', host, '-P', str(port), '-u', user,
        '--result-file', output_file,
    ]
    if single_transaction:
        cmd.append('--single-transaction')
    if routines:
        cmd.append('--routines')
    cmd.append(database)

    env = os.environ.copy()
    # MYSQL_PWD from env or --defaults-file

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, env=env)
        if result.returncode == 0:
            size = os.path.getsize(output_file) if os.path.exists(output_file) else 0
            logger.info(f"MySQL backup complete: {output_file} ({size} bytes)")
            return {'file': output_file, 'size_bytes': size, 'status': 'ok'}
        return {'status': 'error', 'error': result.stderr}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Backup timed out'}


def mysql_restore(
    sql_file: str,
    database: str,
    host: str = 'localhost',
    port: int = 3306,
    user: str = 'root'
) -> Dict[str, Any]:
    """Restore a MySQL backup."""
    cmd = f"mysql -h {host} -P {port} -u {user} {database} < {sql_file}"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3600)
    if result.returncode == 0:
        return {'status': 'ok', 'database': database}
    return {'status': 'error', 'error': result.stderr}


if __name__ == "__main__":
    print("MySQL Backup — Usage Examples")
    print("""
    mysqldump('mydb', '/backups', host='db.example.com')
    mysql_restore('/backups/mydb_20240115.sql', 'mydb_restore')
    """)
