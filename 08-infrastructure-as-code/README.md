# Module 08: Infrastructure as Code

## Overview

Automate infrastructure provisioning using Terraform, Pulumi, and Ansible. Covers state management, drift detection, and configuration management.

## Subdirectories

| Directory    | Description                  | Key Files                                     |
| ------------ | ---------------------------- | --------------------------------------------- |
| `terraform/` | Terraform CLI wrapper        | State management, drift detection, workspaces |
| `pulumi/`    | Pulumi Automation API        | Stack management, resource lifecycle          |
| `ansible/`   | Ansible playbook & inventory | Playbook runner, dynamic inventory            |

## Prerequisites

```bash
pip install requests boto3
# CLI tools: terraform, pulumi, ansible
```

## Key Interview Topics

1. **Terraform state** — Remote backends, locking, state manipulation
2. **Immutable vs mutable infrastructure** — Replace vs update in place
3. **Drift detection** — Detecting config drift from desired state
4. **Pulumi vs Terraform** — Real programming languages vs HCL
5. **Ansible idempotency** — Desired state vs imperative commands
