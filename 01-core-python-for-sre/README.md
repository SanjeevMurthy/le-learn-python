# Module 01: Core Python for SRE

## Overview

Essential Python patterns and techniques that every DevOps/SRE engineer should master. These patterns form the building blocks for all automation scripts and operational tools.

## 📁 Contents

### error-handling/

| File                      | Description                                      |
| ------------------------- | ------------------------------------------------ |
| `retry_decorators.py`     | Retry logic with exponential backoff and jitter  |
| `circuit_breaker.py`      | Circuit breaker pattern for fault tolerance      |
| `graceful_degradation.py` | Graceful fallback when services are unavailable  |
| `custom_exceptions.py`    | Custom exception hierarchy for DevOps operations |

### async-programming/

| File                          | Description                                  |
| ----------------------------- | -------------------------------------------- |
| `async_api_calls.py`          | Concurrent API calls with asyncio            |
| `concurrent_health_checks.py` | Parallel health checks for multiple services |
| `async_file_operations.py`    | Non-blocking file I/O for log processing     |

### logging-patterns/

| File                        | Description                             |
| --------------------------- | --------------------------------------- |
| `structured_logging.py`     | JSON-formatted structured logging       |
| `context_logging.py`        | Contextual logging with correlation IDs |
| `log_aggregation_client.py` | Client for centralized log aggregation  |
| `log_rotation_examples.py`  | Log file rotation and management        |

### concurrency/

| File                          | Description                                  |
| ----------------------------- | -------------------------------------------- |
| `threading_examples.py`       | Thread-based concurrency for I/O-bound tasks |
| `multiprocessing_examples.py` | Process-based parallelism for CPU-bound work |
| `process_pool_executor.py`    | ProcessPoolExecutor for parallel tasks       |
| `queue_patterns.py`           | Producer-consumer patterns with queues       |

### design-patterns/

| File                   | Description                               |
| ---------------------- | ----------------------------------------- |
| `singleton_pattern.py` | Singleton — shared configuration managers |
| `factory_pattern.py`   | Factory — creating cloud provider clients |
| `observer_pattern.py`  | Observer — event-driven monitoring        |
| `strategy_pattern.py`  | Strategy — interchangeable algorithms     |

## 🎓 Key Interview Topics

- "Explain async vs threading vs multiprocessing — when would you use each?"
- "Design a retry mechanism with exponential backoff"
- "Implement a circuit breaker for API resilience"
- "How do you implement structured logging in production?"
- "What design patterns do you use in DevOps automation?"

## 📖 Further Reading

- [Python asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- [Python logging HOWTO](https://docs.python.org/3/howto/logging.html)
- [concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)
