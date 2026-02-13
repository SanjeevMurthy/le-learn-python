# System Design: CI/CD Pipeline

## Question

Design a CI/CD pipeline for a microservices architecture with 50+ services.

## Architecture

```
Developer → Git Push → CI (Build+Test) → Artifact Registry → CD (Deploy)
                │                                    │
                └→ Security Scan                     └→ Canary → Promote → Production
```

## Key Components

| Stage    | Tools                       | Purpose                      |
| -------- | --------------------------- | ---------------------------- |
| Source   | GitHub/GitLab               | Version control, PR reviews  |
| Build    | GitHub Actions, Jenkins     | Compile, unit test, lint     |
| Security | Trivy, Snyk                 | Vulnerability scanning       |
| Artifact | ECR, Artifactory            | Container images, versioned  |
| Deploy   | ArgoCD, Spinnaker           | GitOps, progressive delivery |
| Verify   | Prometheus, synthetic tests | Post-deploy validation       |

## Design Decisions

1. **GitOps**: Declarative desired state in Git → ArgoCD syncs to cluster
2. **Trunk-based development**: Short-lived branches, feature flags
3. **Canary deployments**: 5% → 25% → 100% with automated rollback on error spike
4. **Immutable artifacts**: Same image from staging → production (no rebuild)

## Scaling Considerations

- Monorepo vs polyrepo: polyrepo with shared CI templates
- Build caching: Docker layer cache, dependency cache
- Parallel pipelines: fan-out tests, fan-in deploy gate

## Interview Follow-ups

1. How do you handle database migrations in CI/CD?
2. How do you implement rollback for a microservice with API contract changes?
3. How do you manage secrets in CI/CD pipelines?
