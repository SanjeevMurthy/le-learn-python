# System Design: Container Orchestration

## Question

Design a container orchestration platform for running 500+ microservices.

## Architecture (Kubernetes-based)

```
Ingress (ALB/Nginx) → K8s Service → Pods (Deployment/StatefulSet)
         │                              │
         └→ Service Mesh (Istio)        └→ PVC (EBS/EFS)
```

## Key Design Areas

| Area          | Approach                                                    |
| ------------- | ----------------------------------------------------------- |
| Scheduling    | Node affinity, taints/tolerations, resource requests/limits |
| Networking    | CNI (Calico/Cilium), NetworkPolicy, Service mesh            |
| Storage       | CSI drivers, StorageClass, dynamic provisioning             |
| Security      | RBAC, PSP/PSA, OPA/Gatekeeper, image scanning               |
| Observability | Prometheus + Grafana, Jaeger traces, Fluentd logs           |

## Multi-tenancy

- **Namespace isolation**: one namespace per team/environment
- **Resource quotas**: CPU/memory limits per namespace
- **Network policies**: deny-all default, explicit allow rules
- **RBAC**: team-scoped roles, no cluster-admin for developers

## Scaling

- **HPA**: CPU/memory/custom metrics auto-scaling
- **VPA**: Right-sizing resource requests
- **Cluster Autoscaler**: Add/remove nodes based on pending pods
- **Karpenter**: Node provisioning based on pod requirements

## Interview Follow-ups

1. How do you handle stateful applications in Kubernetes?
2. How do you implement zero-downtime deployments?
3. What's your disaster recovery strategy for a K8s cluster?
