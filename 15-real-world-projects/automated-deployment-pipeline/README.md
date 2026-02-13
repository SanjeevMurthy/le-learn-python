# Automated Deployment Pipeline

## Overview

End-to-end deployment automation combining Docker builds, container registry management, Kubernetes deployments, health checks, and automated rollback.

## Architecture

```
Git Push → Build Docker Image → Push to Registry → Deploy to K8s → Health Check
                                                        │
                                                        └→ Fail? → Rollback
```

## Key Features

- Multi-stage Docker builds
- Semantic versioning for images
- Canary deployment with traffic shifting
- Automated rollback on health check failure
- Slack notifications for deploy status

## Concepts Used

- Module 03: CI/CD Automation
- Module 07: Artifact Management
- Module 09: Incident Response (rollback)
- Module 14: Notifications (Slack alerts)
