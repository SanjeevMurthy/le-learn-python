# Behavioral Questions: Scaling Challenges

## Story 1: 10x Traffic Spike During Launch

**Situation**: Product launch drove 10x normal traffic. Auto-scaling couldn't keep up — hitting cloud provider limits.

**Task**: Scale the platform to handle the load while maintaining response times.

**Action**:

1. Pre-warmed instances and increased ASG limits before launch
2. Added CloudFront caching for static assets (reduced origin load 60%)
3. Implemented read replicas for database read scaling
4. Added Redis caching for frequently accessed API responses

**Result**: Handled 10x traffic with p99 < 300ms. Established capacity planning process for future launches.

---

## Story 2: Database Scaling Bottleneck

**Situation**: Single PostgreSQL instance reached IOPS limits. Write latency growing, affecting order processing.

**Task**: Scale database writes without application downtime.

**Action**:

1. Implemented connection pooling (PgBouncer) — reduced connections 80%
2. Moved read traffic to replicas
3. Partitioned the largest table (orders) by date range
4. Migrated write-heavy audit logs to separate database

**Result**: Write latency dropped 70%. System handled 3x more orders. Established database scaling playbook.

---

## Tips

- Quantify the problem and result (10x traffic, 70% improvement)
- Show systematic thinking (diagnosis → solution → verification)
- Mention trade-offs (consistency vs availability, cost vs performance)
