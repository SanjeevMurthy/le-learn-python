# Log Parser

## Problem Statement

Build a log parser that processes structured and unstructured log files to extract metrics and detect anomalies.

### Requirements

1. Parse common log formats (syslog, JSON, Apache/Nginx access logs)
2. Extract: error counts, response time percentiles, top error messages
3. Detect anomalies: error rate spikes, unusual patterns
4. Support streaming (line-by-line) processing for large files

### Example Input (Nginx Access Log)

```
10.0.0.1 - - [15/Jan/2024:14:30:00 +0000] "GET /api/users HTTP/1.1" 200 1234 0.045
10.0.0.2 - - [15/Jan/2024:14:30:01 +0000] "POST /api/orders HTTP/1.1" 500 89 2.340
```

### Example Output

```python
{
    'total_requests': 1000,
    'error_rate': 0.05,
    'p99_response_time': 1.2,
    'top_errors': [('/api/orders', 500, 42), ('/api/auth', 401, 15)],
}
```
