# Module 05: Monitoring & Observability

## Overview

Build integrations with Prometheus, Grafana, custom metrics systems, and log aggregation pipelines. Covers querying, alerting, dashboard management, and anomaly detection.

## Subdirectories

| Directory          | Description                                 | Key Files                                      |
| ------------------ | ------------------------------------------- | ---------------------------------------------- |
| `prometheus/`      | Prometheus metric querying and alerting     | API client, PromQL, AlertManager, exporters    |
| `grafana/`         | Grafana dashboard and datasource management | Dashboard API, alerts, snapshots               |
| `custom-metrics/`  | Custom metric collection and publishing     | StatsD, metric publishers, time series         |
| `log-aggregation/` | Centralized log processing                  | Elasticsearch, parsing, correlation, anomalies |

## Prerequisites

```bash
pip install requests prometheus-client elasticsearch
```

## Key Interview Topics

1. **Prometheus architecture** — Pull model, TSDB, scrape targets
2. **PromQL** — Rate, histogram_quantile, aggregation operators
3. **Grafana provisioning** — Dashboard-as-code, datasource API
4. **Observability pillars** — Metrics, logs, traces (and profiles)
5. **Alert fatigue** — Meaningful alerts, SLO-based alerting
