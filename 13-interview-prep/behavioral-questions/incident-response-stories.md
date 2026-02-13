# Behavioral Questions: Incident Response Stories

Use the STAR method: **S**ituation, **T**ask, **A**ction, **R**esult.

---

## Story 1: Production Database Outage

**Situation**: Primary database became unresponsive during peak hours, affecting all API endpoints. 500 error rate jumped to 40%.

**Task**: As the on-call SRE, I needed to restore service within the 15-minute SLA.

**Action**:

1. Confirmed the issue via monitoring dashboards (Grafana, PagerDuty)
2. Identified root cause: disk full due to unrotated WAL files
3. Freed space by archiving old WAL files to S3
4. Initiated failover to read replica while cleaning up
5. Communicated status updates to stakeholders every 5 minutes

**Result**: Service restored in 12 minutes (within SLA). Post-mortem led to: automated WAL cleanup cron, disk space alerts at 80%, and runbook for database disk issues.

---

## Story 2: Cascading Failure from Dependency

**Situation**: A third-party payment API started responding slowly (10s+ vs normal 200ms), causing thread pool exhaustion across our API servers.

**Task**: Prevent total outage while maintaining partial service availability.

**Action**:

1. Identified the slow dependency via distributed tracing (Jaeger)
2. Enabled circuit breaker for the payment service (fail-fast)
3. Returned degraded responses (queued payments for later processing)
4. Coordinated with vendor for timeline

**Result**: Non-payment features stayed available. Queued 3,000 payments processed when vendor recovered. Led to implementing circuit breakers on all external dependencies.

---

## Preparation Tips

- Have 3-4 incidents ready with different failure modes
- Emphasize process: detection → communication → mitigation → root cause → prevention
- Show collaboration and communication skills
- Mention specific tools and metrics
- Highlight what you learned and changed as a result
