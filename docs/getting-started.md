# Getting Started

## Prerequisites

- **Python 3.8+** installed
- **pip** or **pipenv** for package management
- **Git** for version control
- Cloud CLI tools (optional):
  - AWS CLI (`aws configure`)
  - gcloud CLI (`gcloud auth application-default login`)
  - kubectl for Kubernetes access

## Setup

### 1. Clone and Install

```bash
git clone <repo-url>
cd le-learn-python

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install core dependencies
pip install -r requirements.txt

# Install dev tools (optional)
pip install -r requirements-dev.txt
```

### 2. Configure Credentials

```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your actual credentials
# At minimum, you need:
# - AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY (for AWS examples)
# - KUBECONFIG (for Kubernetes examples)
# - GITHUB_TOKEN (for CI/CD examples)
```

### 3. Run Your First Example

```bash
# Core Python patterns (no credentials needed)
python 01-core-python-for-sre/error-handling/retry_decorators.py

# Cloud automation (requires AWS credentials)
python 02-cloud-automation/aws/boto3-basics/ec2_management.py

# Kubernetes (requires kubeconfig)
python 03-kubernetes/monitoring/pod_health_checker.py
```

## Module Quick Reference

| If you need...                | Go to...                                 |
| ----------------------------- | ---------------------------------------- |
| Retry logic, circuit breakers | `01-core-python-for-sre/error-handling/` |
| AWS/GCP automation            | `02-cloud-automation/`                   |
| K8s pod management            | `03-kubernetes/client-python-examples/`  |
| CI/CD pipeline scripts        | `04-cicd-automation/`                    |
| Monitoring/alerting           | `05-monitoring-observability/`           |
| Secret management             | `06-secret-management/`                  |
| Interview practice            | `13-interview-prep/`                     |

## Next Steps

1. Browse the module that interests you most
2. Read the module's `README.md` for context
3. Study the code examples with inline comments
4. Try modifying examples for your own use cases
5. Review the interview questions in docstrings
