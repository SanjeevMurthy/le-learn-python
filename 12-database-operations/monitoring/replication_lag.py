"""
replication_lag.py

Monitor database replication lag.

Prerequisites:
- psycopg2 (pip install psycopg2-binary)
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_postgres_replication_lag(
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres',
    database: str = 'postgres'
) -> List[Dict[str, Any]]:
    """
    Check PostgreSQL streaming replication lag.

    Interview Question:
        Q: How do you monitor and handle replication lag?
        A: Metrics: bytes lag (WAL position diff), time lag.
           Query: pg_stat_replication on primary.
           Causes: slow replica (disk I/O), network, heavy writes.
           Impact: stale reads from replica, failover data loss.
           Mitigation: synchronous replication (strong consistency,
           higher latency), monitoring + alerting, read-your-writes
           pattern (route writes to primary, reads to replica).
    """
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, dbname=database)
        cur = conn.cursor()

        cur.execute("""
            SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn,
                   replay_lsn, sync_state,
                   pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
            FROM pg_stat_replication
        """)

        columns = ['client_addr', 'state', 'sent_lsn', 'write_lsn',
                    'flush_lsn', 'replay_lsn', 'sync_state', 'lag_bytes']
        replicas = [dict(zip(columns, row)) for row in cur.fetchall()]

        for r in replicas:
            r['lag_mb'] = round(r['lag_bytes'] / (1024 * 1024), 2) if r['lag_bytes'] else 0
            r['critical'] = r['lag_bytes'] > 100 * 1024 * 1024 if r['lag_bytes'] else False

        cur.close()
        conn.close()
        return replicas
    except ImportError:
        return [{'error': 'psycopg2 not installed'}]
    except Exception as e:
        return [{'error': str(e)}]


def check_replica_lag_from_replica(
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres',
    database: str = 'postgres'
) -> Dict[str, Any]:
    """Check lag from the replica's perspective."""
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, dbname=database)
        cur = conn.cursor()

        cur.execute("""
            SELECT CASE
                WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn()
                THEN 0
                ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
            END AS lag_seconds
        """)
        lag = cur.fetchone()[0]

        cur.close()
        conn.close()
        return {'lag_seconds': round(float(lag), 2), 'critical': float(lag) > 30}
    except ImportError:
        return {'error': 'psycopg2 not installed'}
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    print("Replication Lag Monitor — Usage Examples")
    print("""
    replicas = check_postgres_replication_lag(host='primary.example.com')
    for r in replicas:
        status = '🔴' if r.get('critical') else '🟢'
        print(f"  {status} {r['client_addr']}: {r['lag_mb']}MB lag")
    """)
