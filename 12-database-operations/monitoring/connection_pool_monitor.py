"""
connection_pool_monitor.py

Database connection pool monitoring.

Prerequisites:
- psutil (pip install psutil)
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_postgres_connections(
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres',
    database: str = 'postgres'
) -> Dict[str, Any]:
    """
    Check PostgreSQL connection statistics.

    Interview Question:
        Q: How do you size a connection pool?
        A: Formula: connections = (core_count * 2) + spindle_count.
           For SSDs, ~(core_count * 2) is a good start.
           Too few: queued requests, latency spikes.
           Too many: context switching, memory waste (each PG conn ~10MB).
           PgBouncer: transaction-level pooling (100s of clients → few DB conns).
           Monitor: active vs idle connections, wait time for connection.
           K8s gotcha: many pods × pool_size can exceed max_connections.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, dbname=database)
        cur = conn.cursor()

        # Active connections
        cur.execute("""
            SELECT state, count(*)
            FROM pg_stat_activity
            WHERE datname = current_database()
            GROUP BY state
        """)
        states = dict(cur.fetchall())

        # Max connections
        cur.execute("SHOW max_connections")
        max_conns = int(cur.fetchone()[0])

        total = sum(states.values())
        cur.close()
        conn.close()

        return {
            'max_connections': max_conns,
            'total_active': total,
            'utilization_pct': round(total / max_conns * 100, 1),
            'by_state': states,
            'warning': total > max_conns * 0.8,
        }
    except ImportError:
        return {'error': 'psycopg2 not installed'}
    except Exception as e:
        return {'error': str(e)}


def check_pgbouncer_stats(host: str = 'localhost', port: int = 6432) -> Dict[str, Any]:
    """Check PgBouncer pool statistics."""
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user='pgbouncer', dbname='pgbouncer')
        conn.autocommit = True
        cur = conn.cursor()

        cur.execute("SHOW POOLS")
        columns = [desc[0] for desc in cur.description]
        pools = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.close()
        conn.close()
        return {'pools': pools, 'status': 'ok'}
    except ImportError:
        return {'error': 'psycopg2 not installed'}
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    print("Connection Pool Monitor — Usage Examples")
    print("""
    stats = check_postgres_connections(host='db.example.com')
    print(f"Connections: {stats['total_active']}/{stats['max_connections']}")
    print(f"Utilization: {stats['utilization_pct']}%")
    """)
