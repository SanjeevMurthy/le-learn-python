# Module 11: Networking

## Overview

Network automation, diagnostics, load balancing, and service mesh configuration. Covers port scanning, DNS resolution, Nginx/HAProxy management, and Istio traffic management.

## Subdirectories

| Directory              | Description        | Key Files                        |
| ---------------------- | ------------------ | -------------------------------- |
| `network-diagnostics/` | Connectivity tools | Port scanner, DNS, SSL, latency  |
| `load-balancing/`      | LB configuration   | Nginx, HAProxy, health checks    |
| `service-mesh/`        | Service mesh       | Istio config, traffic management |

## Prerequisites

```bash
pip install requests dnspython
```

## Key Interview Topics

1. **OSI model** — Layer-by-layer troubleshooting
2. **DNS resolution** — A, AAAA, CNAME, TTL, caching
3. **Load balancing algorithms** — Round-robin, least connections, IP hash
4. **Service mesh** — Sidecar proxy, mTLS, traffic splitting
5. **Network policies** — K8s NetworkPolicy, zero-trust
