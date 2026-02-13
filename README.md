# DevOps/SRE Python Toolkit

> A comprehensive collection of Python scripts and examples for DevOps/SRE engineers (6-8 years experience) — practical automation toolkit **and** interview preparation guide.

---

## 🎯 Purpose

This repository serves dual purposes:

1. **Practical Toolkit** — Production-ready Python scripts for day-to-day DevOps/SRE work
2. **Interview Prep** — Coding challenges, system design scenarios, and behavioral question frameworks

## 📚 What's Inside

| Module                                                          | Description                                                     |
| --------------------------------------------------------------- | --------------------------------------------------------------- |
| [01 — Core Python for SRE](01-core-python-for-sre/)             | Async programming, error handling, design patterns, concurrency |
| [02 — Cloud Automation](02-cloud-automation/)                   | AWS (boto3), GCP, Azure integrations                            |
| [03 — Kubernetes](03-kubernetes/)                               | Pod management, monitoring, automation, troubleshooting         |
| [04 — CI/CD Automation](04-cicd-automation/)                    | GitHub Actions, Jenkins, GitLab, deployment strategies          |
| [05 — Monitoring & Observability](05-monitoring-observability/) | Prometheus, Grafana, custom metrics, log aggregation            |
| [06 — Secret Management](06-secret-management/)                 | HashiCorp Vault, secret rotation, encryption                    |
| [07 — Artifact Management](07-artifact-management/)             | JFrog Artifactory, Docker Registry                              |
| [08 — Infrastructure as Code](08-infrastructure-as-code/)       | Terraform, Pulumi, Ansible                                      |
| [09 — Incident Response](09-incident-response/)                 | Runbooks, auto-remediation, post-mortem tooling                 |
| [10 — Performance Optimization](10-performance-optimization/)   | Profiling, caching, load testing                                |
| [11 — Networking](11-networking/)                               | Network diagnostics, load balancing, service mesh               |
| [12 — Database Operations](12-database-operations/)             | Backup/restore, monitoring, migrations                          |
| [13 — Interview Prep](13-interview-prep/)                       | Coding challenges, system design, behavioral questions          |
| [14 — Utilities](14-utilities/)                                 | CLI tools, config management, notifications, data processing    |
| [15 — Real-World Projects](15-real-world-projects/)             | Complete working projects and blueprints                        |

## 🚀 Quick Start

```bash
# Clone repository
git clone <repo-url>
cd le-learn-python

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your credentials

# Run any example
python 01-core-python-for-sre/error-handling/retry_decorators.py
```

## 🎓 Learning Paths

### Path 1: Interview Focused (4 weeks)

1. **Week 1** — Core patterns (retry, circuit breaker, async)
2. **Week 2** — System design (monitoring, deployment pipelines)
3. **Week 3** — Cloud & Kubernetes (AWS, GCP, K8s automation)
4. **Week 4** — Practice mock interviews with examples

### Path 2: Structured (12 weeks)

1. **Week 1-2** — Core Python foundations
2. **Week 3-4** — Cloud automation (AWS + GCP)
3. **Week 5-6** — Kubernetes & containers
4. **Week 7-8** — CI/CD & monitoring
5. **Week 9-10** — Secrets & security
6. **Week 11-12** — IaC, incident response, interview prep

## 📖 Documentation

- [Getting Started Guide](docs/getting-started.md)
- [Interview Prep Roadmap](docs/interview-prep-roadmap.md)
- [API Authentication Guide](docs/api-authentication-guide.md)
- [Best Practices](docs/best-practices.md)
- [Troubleshooting Guide](docs/troubleshooting-guide.md)

## 🔑 Code Principles

- ✅ **Simple functions** — functional programming style, classes only when managing stateful API clients
- ✅ **Extensive inline comments** — explains every logical step and _why_, not just _what_
- ✅ **Type hints** — Python 3.8+ type annotations on all functions
- ✅ **Google-style docstrings** — with interview questions embedded
- ✅ **Error handling** — production-ready patterns with proper logging
- ✅ **Both AWS & GCP** — side-by-side cloud examples for comparison

## 🔐 Security

- Never hardcode credentials — always use environment variables or secret managers
- `.env.example` provided as a template
- All sensitive operations include audit logging patterns

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
