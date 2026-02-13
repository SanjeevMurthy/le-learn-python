"""
mongodb_backup.py

MongoDB backup automation.

Prerequisites:
- subprocess (for mongodump)
"""

import subprocess
import os
import logging
from datetime import datetime
from typing import Dict, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def mongodump(
    database: str,
    output_dir: str,
    host: str = 'localhost',
    port: int = 27017,
    uri: str = '',
    oplog: bool = True
) -> Dict[str, Any]:
    """
    Perform a MongoDB backup.

    Interview Question:
        Q: How do you back up a MongoDB replica set?
        A: mongodump --oplog: captures oplog entries during dump
           for point-in-time consistency.
           Filesystem snapshot: consistent if journaling enabled.
           Cloud: Atlas continuous backups, queryable snapshots.
           Sharded: must use mongos or back up each shard + config server.
           Best practice: back up from secondary to avoid primary load.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = os.path.join(output_dir, f'mongo_{database}_{timestamp}')

    cmd = ['mongodump', '--out', output_path]

    if uri:
        cmd.extend(['--uri', uri])
    else:
        cmd.extend(['--host', host, '--port', str(port)])

    cmd.extend(['--db', database])

    if oplog:
        cmd.append('--oplog')

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            logger.info(f"MongoDB backup complete: {output_path}")
            return {'path': output_path, 'status': 'ok'}
        return {'status': 'error', 'error': result.stderr}
    except subprocess.TimeoutExpired:
        return {'status': 'error', 'error': 'Backup timed out'}


def mongorestore(
    dump_path: str,
    database: str,
    host: str = 'localhost',
    port: int = 27017,
    drop: bool = True
) -> Dict[str, Any]:
    """Restore a MongoDB backup."""
    cmd = ['mongorestore', '--host', host, '--port', str(port), '--db', database]
    if drop:
        cmd.append('--drop')
    cmd.append(dump_path)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
    if result.returncode == 0:
        return {'status': 'ok', 'database': database}
    return {'status': 'error', 'error': result.stderr}


if __name__ == "__main__":
    print("MongoDB Backup — Usage Examples")
    print("""
    mongodump('mydb', '/backups', host='mongo.example.com')
    mongorestore('/backups/mongo_mydb_20240115', 'mydb_restore')
    """)
