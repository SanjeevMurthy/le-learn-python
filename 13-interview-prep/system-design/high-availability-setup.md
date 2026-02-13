# System Design: High Availability Setup

## Question

Design a highly available web application with 99.99% uptime SLA.

## Architecture

```
Route53 (DNS failover) → CloudFront (CDN)
    ├→ Region A: ALB → ECS/EKS → RDS Multi-AZ → ElastiCache
    └→ Region B: ALB → ECS/EKS → RDS Read Replica → ElastiCache
```

## Key Principles

| Principle        | Implementation                               |
| ---------------- | -------------------------------------------- |
| Redundancy       | Multi-AZ, multi-region                       |
| Failover         | DNS failover, database promotion             |
| Load balancing   | ALB across AZs, global with Route53          |
| Data replication | RDS Multi-AZ (sync), cross-region (async)    |
| Caching          | ElastiCache for read-heavy workloads         |
| Circuit breaking | Service mesh, client-side retry with backoff |

## SLA Calculations

| Uptime | Downtime/year | Downtime/month |
| ------ | ------------- | -------------- |
| 99.9%  | 8.76 hours    | 43.8 minutes   |
| 99.95% | 4.38 hours    | 21.9 minutes   |
| 99.99% | 52.6 minutes  | 4.38 minutes   |

## Failure Scenarios and Mitigations

1. **Single server failure**: Auto-scaling replaces, LB routes away
2. **AZ failure**: Multi-AZ deployment, automatic failover
3. **Region failure**: DNS failover to secondary region (RPO/RTO trade-off)
4. **Database failure**: Multi-AZ standby promotion (RDS: ~60s)
5. **Deployment failure**: Canary with automated rollback

## Interview Follow-ups

1. How do you handle split-brain in multi-region setups?
2. What's the trade-off between RPO and RTO?
3. How do you test your HA setup? (Game Days, Chaos Engineering)
