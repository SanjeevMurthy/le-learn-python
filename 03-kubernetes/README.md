# Module 03: Kubernetes Automation

## Overview

Automate Kubernetes cluster operations using the Python kubernetes client. Covers pod management, deployment operations, monitoring, automated remediation, troubleshooting, and Helm chart management.

## Subdirectories

| Directory                 | Description               | Key Files                                                   |
| ------------------------- | ------------------------- | ----------------------------------------------------------- |
| `client-python-examples/` | Core K8s API operations   | Pods, Deployments, Services, ConfigMaps, Namespaces, CRDs   |
| `monitoring/`             | Cluster health monitoring | Pod health, resource usage, event watching, node status     |
| `automation/`             | Operational automation    | Rolling restarts, scaling, node draining, backup/restore    |
| `troubleshooting/`        | Debugging tools           | Pod diagnostics, network debugging, log aggregation, quotas |
| `helm/`                   | Helm chart management     | Helm client wrapper, chart lifecycle                        |

## Prerequisites

```bash
pip install kubernetes
# Optional: for Helm operations
pip install pyhelm  # or use subprocess with helm CLI
```

## Key Interview Topics

1. **K8s API model** — How watch, list, patch work under the hood
2. **Pod lifecycle** — Init containers, readiness/liveness probes, restart policies
3. **Deployment strategies** — Rolling update, recreate, blue-green, canary
4. **Resource management** — Requests, limits, quotas, LimitRanges
5. **Service discovery** — ClusterIP, NodePort, LoadBalancer, Ingress
6. **RBAC** — ServiceAccounts, Roles, ClusterRoles, RoleBindings
7. **Helm** — Chart structure, values, hooks, rollback

## Quick Start

```python
# Uses ~/.kube/config by default (same as kubectl)
from kubernetes import client, config
config.load_kube_config()
v1 = client.CoreV1Api()
pods = v1.list_pod_for_all_namespaces()
```
