"""
query_performance.py

Database query performance analysis.

Prerequisites:
- psycopg2 (pip install psycopg2-binary)
"""

import logging
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_slow_queries(
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres',
    database: str = 'postgres',
    min_duration_ms: int = 1000
) -> List[Dict[str, Any]]:
    """
    Find slow queries from pg_stat_statements.

    Interview Question:
        Q: How do you optimize slow database queries?
        A: 1. EXPLAIN ANALYZE: show execution plan with actual timings
           2. Check for sequential scans on large tables → add indexes
           3. N+1 queries: use JOINs or batch loading
           4. pg_stat_statements: track query frequency + avg time
           5. Index types: B-tree (default), GIN (full-text), GiST (geo)
           6. Common fixes: add missing indexes, rewrite subqueries
              as JOINs, use LIMIT, add WHERE clauses, partition large tables.
    """
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, dbname=database)
        cur = conn.cursor()

        cur.execute("""
            SELECT query, calls, mean_exec_time, total_exec_time, rows
            FROM pg_stat_statements
            WHERE mean_exec_time > %s
            ORDER BY total_exec_time DESC
            LIMIT 20
        """, (min_duration_ms,))

        columns = ['query', 'calls', 'mean_time_ms', 'total_time_ms', 'rows']
        results = [dict(zip(columns, row)) for row in cur.fetchall()]

        cur.close()
        conn.close()
        return results
    except ImportError:
        return [{'error': 'psycopg2 not installed'}]
    except Exception as e:
        return [{'error': str(e)}]


def explain_query(
    query: str,
    host: str = 'localhost',
    port: int = 5432,
    user: str = 'postgres',
    database: str = 'postgres'
) -> Dict[str, Any]:
    """Run EXPLAIN ANALYZE on a query."""
    try:
        import psycopg2
        conn = psycopg2.connect(host=host, port=port, user=user, dbname=database)
        cur = conn.cursor()

        cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
        plan = cur.fetchone()[0]

        cur.close()
        conn.close()
        return {'plan': plan, 'status': 'ok'}
    except ImportError:
        return {'error': 'psycopg2 not installed'}
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    print("Query Performance — Usage Examples")
    print("""
    slow = get_slow_queries(host='db.example.com', min_duration_ms=500)
    for q in slow:
        print(f"  {q['mean_time_ms']:.0f}ms avg, {q['calls']} calls: {q['query'][:80]}")
    """)
