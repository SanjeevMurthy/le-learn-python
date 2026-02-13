# Module 12: Database Operations

## Overview

Automate database backup/restore, monitoring, and migrations. Covers PostgreSQL, MySQL, MongoDB backups, connection pool monitoring, query performance, replication lag, and schema/data migrations.

## Subdirectories

| Directory         | Description       | Key Files                                 |
| ----------------- | ----------------- | ----------------------------------------- |
| `backup-restore/` | Backup automation | PostgreSQL, MySQL, MongoDB, PITR          |
| `monitoring/`     | DB monitoring     | Connection pools, query perf, replication |
| `migrations/`     | Schema & data     | Schema migration, data migration          |

## Prerequisites

```bash
pip install psycopg2-binary pymysql pymongo
```

## Key Interview Topics

1. **Backup strategies** — Full, incremental, differential, WAL archiving
2. **Point-in-time recovery** — WAL replay, binlog position
3. **Connection pooling** — PgBouncer, ProxySQL, pool sizing
4. **Query optimization** — EXPLAIN ANALYZE, index strategies
5. **Replication** — Streaming replication, lag, failover
