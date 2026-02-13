# Best Practices

## 🔐 Security

### Never Hardcode Credentials

```python
# ❌ WRONG
API_KEY = "sk-12345"

# ✅ CORRECT
import os
API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

### Validate All Inputs

```python
def process_instance(instance_id: str) -> None:
    # Validate input format
    if not instance_id.startswith('i-'):
        raise ValueError(f"Invalid instance ID format: {instance_id}")
```

### Log Securely

```python
# ❌ WRONG - exposes secrets
logger.info(f"Connecting with password: {password}")

# ✅ CORRECT - mask sensitive data
logger.info(f"Connecting to database as user: {username}")
```

---

## 🧪 Testing

### Mock External APIs

```python
from unittest.mock import patch, Mock

@patch('boto3.client')
def test_list_instances(mock_client):
    mock_client.return_value.describe_instances.return_value = {
        'Reservations': []
    }
    result = list_instances_by_tag('env', 'dev')
    assert result == []
```

### Use Fixtures for Common Setup

```python
import pytest

@pytest.fixture
def sample_pod_status():
    return {
        'pod_name': 'test-pod',
        'restart_count': 10,
        'status': 'CrashLoopBackOff'
    }
```

---

## 📝 Code Style

### Type Hints

```python
from typing import List, Dict, Optional

def find_resources(
    tag_key: str,
    tag_value: str,
    region: str = 'us-east-1'
) -> List[Dict]:
    ...
```

### Google-Style Docstrings

```python
def create_backup(instance_id: str, retention_days: int = 7) -> Dict:
    """
    Create a backup of the specified instance.

    Args:
        instance_id: EC2 instance ID (e.g., 'i-1234567890abcdef0')
        retention_days: How many days to retain the backup

    Returns:
        Dictionary with backup details including backup_id and expiry_date

    Raises:
        ValueError: If instance_id format is invalid
        boto3.exceptions.ClientError: If AWS API call fails
    """
```

### Inline Comments — Explain _Why_

```python
# ❌ WRONG - states the obvious
x = x + 1  # increment x

# ✅ CORRECT - explains the reason
delay *= backoff_factor  # Increase delay exponentially to avoid thundering herd
```

---

## 🔄 Error Handling

### Use Specific Exceptions

```python
# ❌ WRONG
try:
    result = api_call()
except Exception:
    pass

# ✅ CORRECT
try:
    result = api_call()
except requests.ConnectionError:
    logger.error("Network error - check connectivity")
    raise
except requests.HTTPError as e:
    logger.error(f"API returned error: {e.response.status_code}")
    raise
```

### Always Log Before Re-raising

```python
try:
    response = client.describe_instances()
except ClientError as e:
    logger.error(f"Failed to describe instances: {e}")
    raise  # always re-raise so caller knows
```

---

## 📊 Logging

### Use Structured Logging

```python
import structlog

logger = structlog.get_logger()
logger.info("instance_stopped", instance_id="i-123", region="us-east-1")
```

### Log Levels Matter

- `DEBUG` — detailed diagnostic info
- `INFO` — confirmation that things work as expected
- `WARNING` — something unexpected but not an error
- `ERROR` — a failure that needs attention
- `CRITICAL` — the program cannot continue
