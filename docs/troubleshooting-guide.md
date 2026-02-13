# Troubleshooting Guide

## Common Setup Issues

### Python Version Mismatch

```bash
# Check your Python version
python3 --version

# This toolkit requires Python 3.8+
# If using older version, upgrade:
brew install python@3.11  # macOS
```

### Virtual Environment Issues

```bash
# If venv creation fails
python3 -m pip install --upgrade pip
python3 -m venv venv --clear  # recreate from scratch
```

### Import Errors

```bash
# If a module can't be found
pip install -r requirements.txt  # reinstall all deps

# For specific cloud SDKs
pip install boto3        # AWS
pip install kubernetes   # K8s
pip install hvac         # Vault
```

---

## Cloud Authentication Issues

### AWS: "NoCredentialsError"

```bash
# Verify credentials are configured
aws sts get-caller-identity

# If not configured
aws configure
```

### GCP: "DefaultCredentialsError"

```bash
# Log in with application default credentials
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Kubernetes: "ConfigException"

```bash
# Verify cluster access
kubectl cluster-info

# If not configured, set context
kubectl config use-context your-cluster
```

---

## Runtime Issues

### Rate Limiting

If you see `429 Too Many Requests`:

- All examples include retry logic with exponential backoff
- Reduce the frequency of API calls
- Check API rate limits for each service

### Timeout Errors

```python
# Increase timeout in requests
response = requests.get(url, timeout=30)  # increase from default 5

# For Kubernetes operations
config.load_kube_config()
# Set request_timeout in API calls
```

### Memory Issues with Large Datasets

```python
# Use pagination instead of loading all at once
paginator = ec2_client.get_paginator('describe_instances')
for page in paginator.paginate():
    process(page)
```

---

## Getting Help

1. Check the module's `README.md` for prerequisites
2. Look at inline comments in the code for common pitfalls
3. Check the `.env.example` for required environment variables
4. Review [API Authentication Guide](api-authentication-guide.md)
