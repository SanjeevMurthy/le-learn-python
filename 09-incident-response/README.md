# Module 09: Incident Response

## Overview

Automate incident response with runbooks, auto-remediation, and post-mortem tooling. Covers common failure scenarios, automated recovery, and blameless post-mortems.

## Subdirectories

| Directory      | Description            | Key Files                                       |
| -------------- | ---------------------- | ----------------------------------------------- |
| `runbooks/`    | Investigation runbooks | CPU, memory, disk, network troubleshooting      |
| `automation/`  | Auto-remediation       | Rollback, emergency scaling, service restart    |
| `post-mortem/` | Post-incident analysis | Timeline, metrics collection, report generation |

## Prerequisites

```bash
pip install psutil requests
```

## Key Interview Topics

1. **Incident management process** — Detect → triage → mitigate → resolve → post-mortem
2. **SLO/SLA/SLI** — Service level objectives and error budgets
3. **On-call best practices** — Runbooks, escalation, paging fatigue
4. **Blameless post-mortems** — Root cause analysis, action items
5. **Chaos engineering** — Proactive failure injection
