# Module 01 — Core Python for SRE: Interview Questions

## Error Handling & Resilience

### 1. Retry Patterns

**Q: When would you implement retry logic and what pitfalls should you avoid?**

A: Implement retries for transient failures (network timeouts, rate limits, temporary service unavailability). Pitfalls:

- **Retry storms**: If all clients retry at the same time, it can overwhelm the service. Use **jitter** (random delay) to spread retries.
- **Retrying non-idempotent operations**: Retrying a POST that creates a record can cause duplicates. Only retry idempotent operations (GET, PUT, DELETE).
- **No backoff**: Fixed-interval retries don't give the service time to recover. Use **exponential backoff** (1s, 2s, 4s, 8s...).
- **Infinite retries**: Always set a maximum retry count with alerting.

**Q: Explain exponential backoff with jitter. Why is jitter important?**

A: Exponential backoff increases wait time exponentially between retries (e.g., 1s → 2s → 4s). Jitter adds randomness to the delay. Without jitter, all clients that failed at the same time will also retry at the same time (thundering herd problem), potentially causing the service to fail again.

---

### 2. Circuit Breaker Pattern

**Q: What is the circuit breaker pattern and what states does it have?**

A: Circuit breaker prevents cascading failures by stopping calls to a failing service:

- **CLOSED** (normal): Requests pass through. Track failures.
- **OPEN** (tripped): Requests fail immediately without calling the service. Prevents overloading a struggling service.
- **HALF-OPEN** (testing): After a timeout, allow one test request. If it succeeds, go to CLOSED. If it fails, go back to OPEN.

**Q: How do you choose the failure threshold and recovery timeout?**

A: Base it on the service's SLA and recovery patterns:

- **Failure threshold**: If the service's error budget allows 0.1% errors, set threshold at 5-10 consecutive failures.
- **Recovery timeout**: Match the service's typical recovery time. Start with 30-60 seconds and tune based on observed behavior.
- **Monitor**: Track circuit breaker state changes as metrics — frequent OPEN states indicate a systemic problem.

---

### 3. Graceful Degradation

**Q: What is graceful degradation vs fail-fast?**

A: **Graceful degradation**: When a dependency fails, return reduced functionality instead of an error. Example: show cached data when the database is down.
**Fail-fast**: Immediately return an error when a dependency fails. Better for critical operations where partial/stale data is unacceptable (e.g., financial transactions).

**Q: Design a multi-tier fallback for a user profile service.**

A: Primary DB → Read replica → Redis cache → CDN cached response → Static default profile. Each tier has different consistency guarantees. Log which tier served the request for monitoring.

---

### 4. Custom Exceptions

**Q: Why create custom exception hierarchies?**

A: 1. **Distinguishes** your errors from system/library errors 2. **Adds context** (instance ID, region, operation name) 3. **Enables targeted handling** (retry transient errors, alert on permanent ones) 4. **Machine-readable** error codes for monitoring dashboards 5. **Clean separation** between cloud provider, Kubernetes, and CI/CD errors

---

## Async Programming

### 5. asyncio

**Q: How does async/await differ from threading for I/O-bound tasks?**

A: Async uses a single thread with cooperative multitasking — coroutines voluntarily yield control at `await` points. Threading uses OS-level threads with preemptive scheduling.

- **Async**: Lighter (no thread overhead), avoids race conditions, scales better for many concurrent I/O operations (1000+ connections)
- **Threading**: Works with blocking libraries (boto3, requests), simpler mental model
- **Rule of thumb**: Use async when you have async-native libraries; use threading when calling blocking code.

**Q: What is `asyncio.Semaphore` and when would you use one?**

A: A semaphore limits the number of concurrent operations. Think of it as a token bucket — only N coroutines can proceed at once. Use it to prevent overwhelming a service with too many concurrent requests (e.g., limit to 20 concurrent API calls).

---

## Logging Patterns

### 6. Structured Logging

**Q: Why use structured (JSON) logging instead of plain text?**

A: 1. **Machine-parseable** — ELK/Splunk/CloudWatch can index fields automatically 2. **Searchable** — query by any field (`user_id=123`, `request_id=abc`) 3. **Consistent** — uniform format across all microservices 4. **Rich context** — attach metadata without format string gymnastics 5. **Alertable** — trigger alerts on specific field values

### 7. Correlation IDs

**Q: How do you trace a request across microservices?**

A: Generate a unique correlation ID at the entry point (API gateway), pass it via HTTP header (`X-Correlation-ID`), include it in every log entry, pass it to downstream services. This lets you search all logs from a single user request across all services.

In Python, use `ContextVar` to store the correlation ID — it's thread-safe and works with asyncio.

---

## Concurrency

### 8. Threading vs Multiprocessing

**Q: When would you use threading vs multiprocessing vs asyncio?**

A:
| Approach | Best For | GIL Impact | Overhead |
|----------|----------|------------|----------|
| Threading | I/O-bound (API calls, file I/O) | GIL released during I/O | Medium |
| Multiprocessing | CPU-bound (parsing, hashing) | Each process has own GIL | High |
| asyncio | High-concurrency I/O | Single thread | Low |

**Q: What is the GIL?**

A: The Global Interpreter Lock prevents multiple Python threads from executing Python bytecode simultaneously. It's released during I/O operations, so threading works for I/O-bound tasks. For CPU-bound work, use multiprocessing (each process has its own GIL).

### 9. Producer-Consumer Pattern

**Q: Explain the producer-consumer pattern.**

A: Decouples production from consumption using a buffer (queue). Producer adds work items without waiting for processing; consumers pull and process independently. Benefits: load leveling, different processing speeds, crash isolation. The queue acts as a shock absorber.

### 10. Thread Safety

**Q: Explain race conditions and how to prevent them.**

A: A race condition occurs when 2+ threads access shared data concurrently and at least one modifies it. Prevent with:

1. **Locks/Mutexes** — exclusive access to critical sections
2. **Atomic operations** — single indivisible operations
3. **Thread-local storage** — each thread has its own copy
4. **Immutable data** — no modification possible
5. **Queue-based communication** — avoid shared state entirely

---

## Design Patterns

### 11. Singleton

**Q: When would you use Singleton in DevOps tools?**

A: Configuration managers (one source of truth), connection pools (shared resource), rate limiters (global state). In Python, prefer module-level functions with globals over class-based Singleton — it's simpler and more Pythonic.

### 12. Factory

**Q: What is the Factory pattern?**

A: Factory encapsulates object creation logic, decoupling callers from specific implementations. Use when: object creation is complex, you support multiple implementations (AWS/GCP/Azure), or you want to swap implementations for testing.

### 13. Observer

**Q: What is the Observer pattern?**

A: Decouples event producers from consumers. Producers emit events; observers react independently. DevOps uses: monitoring alerts (metric → Slack, PagerDuty, email), CI/CD events (build done → deploy + notify), infrastructure changes (resource created → audit + tag).

### 14. Strategy

**Q: Compare rolling, blue-green, and canary deployment strategies.**

A:

- **Rolling**: Gradual replacement, no extra infrastructure, risk of mixed versions during deploy
- **Blue-Green**: Two identical environments, instant switchover, fast rollback, but 2x infrastructure cost
- **Canary**: Small % of traffic to new version first, validate metrics, then increase. Low risk but complex routing.

---

## Coding Challenges

1. Implement a retry decorator with exponential backoff and jitter
2. Build a circuit breaker that transitions between CLOSED, OPEN, and HALF-OPEN states
3. Design a multi-tier fallback system with caching
4. Create a thread-safe producer-consumer pipeline
5. Implement a priority queue-based job scheduler
6. Build a structured logging system with correlation IDs
7. Design a factory that creates cloud clients for AWS/GCP/Azure
8. Implement an observer-based monitoring alert system
