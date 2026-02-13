# Module 07: Artifact Management

## Overview

Manage build artifacts using JFrog Artifactory and Docker registries. Covers upload/download, repository management, cleanup policies, and vulnerability scanning.

## Subdirectories

| Directory            | Description                | Key Files                                      |
| -------------------- | -------------------------- | ---------------------------------------------- |
| `jfrog-artifactory/` | JFrog Artifactory REST API | Upload, download, repos, cleanup, build info   |
| `docker-registry/`   | Docker Registry v2 API     | Image management, scanning, garbage collection |

## Prerequisites

```bash
pip install requests docker
```

## Key Interview Topics

1. **Artifact lifecycle** — Build → store → promote → deploy → cleanup
2. **Immutable artifacts** — Why never overwrite a release artifact
3. **Docker image layers** — Union filesystem, layer caching
4. **Vulnerability scanning** — Shift-left security, CVE databases
5. **Retention policies** — Keep N versions, expire by age
