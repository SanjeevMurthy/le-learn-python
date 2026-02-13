# Module 02: Cloud Automation — Interview Questions

## AWS Core

### 1. boto3 Client vs Resource

**Q: What is the difference between boto3 client and resource?**
A: Client is a low-level API that maps 1:1 to AWS API calls. Resource is a higher-level, object-oriented abstraction. Client gives more control and covers all services. Resource is more Pythonic but doesn't cover all APIs. Production automation typically uses client for consistency.

### 2. EC2 Instance Tagging Strategy

**Q: How do you organize resources across multiple AWS accounts?**
A: Use mandatory tags: Environment, Team/Owner, Application, CostCenter. Enforce with AWS Config rules and tag policies in AWS Organizations. Use tag-based IAM policies for access control.

### 3. S3 Security

**Q: How do you secure an S3 bucket?**
A: Block public access (account + bucket level), encrypt at rest (SSE-S3/KMS), enforce HTTPS via bucket policy, enable versioning, enable access logging, use IAM + bucket policies with least privilege, enable MFA delete for critical buckets.

### 4. S3 Storage Classes

**Q: Explain S3 storage classes and when to use each.**
A: STANDARD (frequent access), INTELLIGENT_TIERING (unknown patterns), STANDARD_IA (infrequent, per-GB retrieval), ONE_ZONE_IA (cheaper, single AZ), GLACIER (archive, minutes-hours retrieval), GLACIER_DEEP_ARCHIVE (cheapest, 12+ hours). Use lifecycle policies to auto-transition.

### 5. Lambda Cold Starts

**Q: How does Lambda cold start work and how do you optimize it?**
A: Cold start = new execution environment creation (download code → init runtime → run init code). Optimize: small packages, init SDK clients outside handler, use provisioned concurrency, choose fast runtimes, use SnapStart (Java).

---

## Cost Optimization

### 6. Automated Cost Savings

**Q: How would you implement automated cost savings for EC2?**
A: Tag instances with AutoStop/AutoStart, Lambda + EventBridge for scheduling, identify idle instances (CPU < 5% for 7 days), right-size using CloudWatch, use Savings Plans/Reserved for prod, Spot for fault-tolerant workloads.

### 7. Cost Visibility

**Q: How do you implement cost visibility across teams?**
A: Mandate cost allocation tags, enable tag-based billing, automate weekly reports via Cost Explorer API, set up AWS Budgets per team, create dashboards, implement showback/chargeback policies.

### 8. Cost Anomaly Detection

**Q: How would you detect cost anomalies automatically?**
A: Track daily costs with moving average, alert if daily > 2x average, use AWS Cost Anomaly Detection (ML-based), monitor expensive services, set budget alerts at 50/80/100%, correlate with deployments.

---

## Security

### 9. IAM Best Practices

**Q: What are the top IAM security best practices?**
A: Enable MFA for all users, use IAM roles (not access keys), apply least-privilege, rotate keys < 90 days, use Organizations SCPs, enable CloudTrail, use IAM Access Analyzer.

### 10. Least Privilege Enforcement

**Q: What is the principle of least privilege and how do you enforce it?**
A: Grant only minimum permissions needed. Enforce: start with zero, add as needed; use scoped policies; add condition keys (IP, MFA); use Access Analyzer for unused permissions; regular reviews; SCPs as guardrails.

### 11. Security Group Auditing

**Q: How would you design a security group audit system?**
A: Enumerate all SGs, check rules against policy, classify by severity (critical: DB ports open to internet), cross-reference with running instances, auto-remediate critical findings, report with remediation guidance.

---

## Multi-Cloud

### 12. GKE vs EKS vs AKS

**Q: Compare GKE, EKS, and AKS.**
A: GKE: most mature, Autopilot mode, best multi-cluster (Anthos), free Autopilot tier. EKS: $0.10/hr control plane, tight AWS integration, Fargate. AKS: free control plane, Azure AD integration, best for Azure orgs. All support managed nodes, auto-scaling, RBAC.

### 13. Cross-Region DR

**Q: Design a cross-region DR strategy for AWS.**
A: Identify critical resources, set RPO/RTO targets, automate cross-region snapshot copies, enable S3 cross-region replication, maintain IaC for DR region, regular DR drills.

### 14. RPO vs RTO

**Q: Explain RPO vs RTO in disaster recovery.**
A: RPO = max acceptable data loss in time (1 hour RPO → hourly backups). RTO = max acceptable downtime (15 min RTO → system back in 15 mins). Lower RPO/RTO = higher cost.

---

## Coding Challenges

1. **Resource Tagger**: Write a function that tags all untagged EC2 instances with a default tag set
2. **Cost Report**: Build a script that generates a daily cost report grouped by service and sends it to Slack
3. **Security Scanner**: Create a multi-region security group scanner that identifies all 0.0.0.0/0 ingress rules
4. **Snapshot Manager**: Implement a snapshot lifecycle manager with creation, retention, and cross-region copy
5. **Multi-Cloud Inventory**: Write a unified inventory function that lists compute instances from AWS, GCP, and Azure
6. **Idle Resource Finder**: Build a script that finds EC2 instances with < 5% CPU over 7 days and recommends action
