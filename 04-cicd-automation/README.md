# Module 04: CI/CD Automation

## Overview

Integrate with popular CI/CD platforms using Python APIs. Covers GitHub Actions, GitLab CI, Jenkins, CircleCI, and deployment strategies (blue-green, canary, rolling).

## Subdirectories

| Directory                | Description             | Key Files                     |
| ------------------------ | ----------------------- | ----------------------------- |
| `github-actions/`        | GitHub Actions REST API | Workflows, artifacts, secrets |
| `gitlab/`                | GitLab CI/CD API        | Pipelines, MRs, variables     |
| `jenkins/`               | Jenkins REST API        | Jobs, builds, plugins, Groovy |
| `circleci/`              | CircleCI API v2         | Pipelines, workflows          |
| `deployment-strategies/` | Deployment patterns     | Blue-green, canary, rolling   |

## Prerequisites

```bash
pip install requests PyGithub python-gitlab python-jenkins
```

## Key Interview Topics

1. **CI vs CD vs CD** — Continuous Integration / Delivery / Deployment
2. **Pipeline design** — Stages, parallelism, caching, artifacts
3. **Deployment strategies** — Trade-offs between blue-green, canary, rolling
4. **Secret management in CI** — Environment variables, masked secrets, OIDC
5. **Pipeline as code** — Declarative vs scripted, reusable workflows
