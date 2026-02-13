# System Design: Monitoring System

## Question

Design a monitoring and alerting system for a large-scale distributed application.

## Requirements

- Collect metrics from 10,000+ servers
- Support custom application metrics
- Alerting with multiple notification channels
- Dashboard visualization
- 90-day metric retention

## High-Level Architecture

```
Exporters → Prometheus (scrape) → AlertManager → PagerDuty/Slack
                │
                └→ Thanos (long-term) → Grafana (visualization)
```

## Key Components

| Component     | Purpose           | Technology                     |
| ------------- | ----------------- | ------------------------------ |
| Collection    | Scrape metrics    | Prometheus, node_exporter      |
| Storage       | Time-series DB    | Prometheus TSDB, Thanos/Cortex |
| Alerting      | Rule evaluation   | AlertManager, PagerDuty        |
| Visualization | Dashboards        | Grafana                        |
| Long-term     | >30 day retention | Thanos with S3                 |

## Design Decisions

1. **Pull vs Push**: Prometheus pull model — simpler, service discovery, no backpressure
2. **Cardinality**: Limit label values (no user IDs in labels — explodes TSDB)
3. **Federation**: Regional Prometheus → global Thanos for cross-DC queries
4. **Alert fatigue**: Symptom-based alerts (user impact), not cause-based

## Scaling Considerations

- **Sharding**: Prometheus per team/service with Thanos for global view
- **Retention**: Hot (Prometheus 15d) → Warm (Thanos 90d) → Cold (S3 archive)
- **High Availability**: Prometheus pair (identical scrapes) + AlertManager cluster

## Interview Follow-ups

1. How would you handle metric cardinality explosion?
2. How do you avoid alert fatigue?
3. Prometheus vs Datadog vs CloudWatch — trade-offs?
