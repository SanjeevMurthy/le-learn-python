# API Authentication Guide

## Overview

This guide covers how to authenticate with the various third-party APIs used in this toolkit.

---

## AWS (boto3)

### Option 1: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export AWS_DEFAULT_REGION=us-east-1
```

### Option 2: AWS CLI Config

```bash
aws configure
# Enter access key, secret key, region, output format
```

### Option 3: IAM Role (EC2/Lambda)

When running on AWS infrastructure, IAM roles are automatically used — no explicit credentials needed.

### Credential Lookup Order

1. Environment variables
2. `~/.aws/credentials` file
3. IAM instance role (if on EC2)

---

## GCP (google-cloud-\*)

### Option 1: Service Account Key

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Option 2: User Credentials

```bash
gcloud auth application-default login
```

### Option 3: Workload Identity (GKE)

Automatic when running on GKE with workload identity configured.

---

## Kubernetes (client-python)

### Option 1: Kubeconfig (External)

```python
from kubernetes import config
config.load_kube_config()  # Uses ~/.kube/config
```

### Option 2: In-Cluster (Pod)

```python
from kubernetes import config
config.load_incluster_config()  # Uses service account
```

---

## GitHub (PyGithub)

```bash
export GITHUB_TOKEN=ghp_your_personal_access_token
```

Required scopes: `repo`, `workflow`, `admin:org` (depending on operations).

---

## Jenkins (python-jenkins)

```python
import jenkins
server = jenkins.Jenkins(
    'http://jenkins.example.com',
    username='admin',
    password='your-api-token'  # Use API token, not password
)
```

Generate API token: Jenkins → User → Configure → API Token → Add new Token.

---

## HashiCorp Vault (hvac)

### Token Auth (Development)

```bash
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='dev-token'
```

### AppRole Auth (Production)

```bash
export VAULT_ADDR='https://vault.example.com'
export VAULT_ROLE_ID='your-role-id'
export VAULT_SECRET_ID='your-secret-id'
```

---

## Prometheus / Grafana

### Prometheus

No auth typically needed for read operations. URL only:

```bash
export PROMETHEUS_URL=http://prometheus:9090
```

### Grafana

```bash
export GRAFANA_URL=http://grafana:3000
export GRAFANA_API_KEY=your-api-key
```

Generate API key: Grafana → Configuration → API Keys → Add API key.

---

## JFrog Artifactory

### API Key

```bash
export ARTIFACTORY_URL=https://your-instance.jfrog.io/artifactory
export ARTIFACTORY_API_KEY=your-api-key
```

### Basic Auth

```bash
export ARTIFACTORY_USER=admin
export ARTIFACTORY_PASSWORD=your-password
```

---

## 🔒 Security Best Practices

1. **Never commit credentials** — use `.env` files excluded by `.gitignore`
2. **Rotate regularly** — change API keys and tokens periodically
3. **Use least privilege** — only grant the permissions each script needs
4. **Prefer short-lived tokens** — use temporary credentials when possible
5. **Audit access** — monitor who is using which credentials
