# Module 02: Cloud Automation

## Overview

Automate cloud infrastructure management across AWS, GCP, and Azure using Python SDKs. Covers instance management, storage operations, cost optimization, security auditing, and automated operations.

## Subdirectories

| Directory                | Description                    | Key Files                                    |
| ------------------------ | ------------------------------ | -------------------------------------------- |
| `aws/boto3-basics/`      | Core AWS SDK operations        | EC2, S3, Lambda, CloudWatch                  |
| `aws/cost-optimization/` | Cost management & savings      | Unused resources, rightsizing, Cost Explorer |
| `aws/security/`          | Security auditing & compliance | IAM audit, security groups, Secrets Manager  |
| `aws/automation/`        | Automated operations           | Backups, AMI lifecycle, auto scaling         |
| `gcp/`                   | Google Cloud Platform          | Compute Engine, Cloud Storage, GKE, Logging  |
| `azure/`                 | Microsoft Azure                | VM management, AKS, Azure Monitor            |

## Prerequisites

```bash
# AWS
pip install boto3

# GCP
pip install google-cloud-compute google-cloud-storage google-cloud-container google-cloud-logging

# Azure
pip install azure-mgmt-compute azure-mgmt-containerservice azure-monitor-query azure-identity
```

## Key Interview Topics

1. **Multi-cloud strategy** — Why and how to abstract provider differences
2. **Cost optimization** — Automated resource cleanup and rightsizing
3. **Security automation** — IAM auditing, policy enforcement, secret rotation
4. **Infrastructure lifecycle** — Backup strategies, AMI management, scaling policies
5. **Cloud SDK patterns** — Pagination, error handling, rate limiting

## Quick Start

```python
# Set AWS credentials (use IAM roles in production)
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="us-east-1"

# Run any example
python aws/boto3-basics/ec2_management.py
```

## Learning Path

1. Start with `aws/boto3-basics/` for SDK fundamentals
2. Move to `aws/cost-optimization/` for practical cost savings
3. Study `aws/security/` for compliance and auditing
4. Review `gcp/` and `azure/` for multi-cloud exposure
5. Use `aws/automation/` patterns for real-world automation

## Files

See `interview_questions.md` for a comprehensive list of interview Q&As covering all cloud automation topics.
