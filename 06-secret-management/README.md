# Module 06: Secret Management

## Overview

Manage secrets securely using HashiCorp Vault, implement secret rotation patterns, and handle encryption at rest and in transit.

## Subdirectories

| Directory          | Description             | Key Files                                      |
| ------------------ | ----------------------- | ---------------------------------------------- |
| `hashicorp-vault/` | Vault client operations | KV secrets, dynamic secrets, transit, policies |
| `secret-rotation/` | Rotation patterns       | DB credentials, API keys, certificates         |
| `encryption/`      | Encryption utilities    | At-rest, in-transit (TLS), key management      |

## Prerequisites

```bash
pip install hvac cryptography requests
```

## Key Interview Topics

1. **Vault architecture** — Sealing/unsealing, auth methods, secret engines
2. **Dynamic secrets** — Short-lived credentials, lease management
3. **Secret zero problem** — How does the first secret get to the app?
4. **Encryption as a service** — Vault Transit backend
5. **Certificate management** — PKI, auto-rotation, mTLS
