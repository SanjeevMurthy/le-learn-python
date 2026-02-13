# Module 10: Performance Optimization

## Overview

Profile, cache, and load-test Python applications and infrastructure. Covers CPU/memory/IO profiling, Redis/Memcached caching patterns, and load testing with Locust.

## Subdirectories

| Directory       | Description             | Key Files                    |
| --------------- | ----------------------- | ---------------------------- |
| `profiling/`    | Python profiling tools  | CPU, memory, I/O profiling   |
| `caching/`      | Caching patterns        | Redis, Memcached, strategies |
| `load-testing/` | Load testing frameworks | Locust, benchmarking         |

## Prerequisites

```bash
pip install redis pymemcache locust psutil memory-profiler
```

## Key Interview Topics

1. **CPU profiling** — cProfile, py-spy, flame graphs
2. **Memory profiling** — tracemalloc, objgraph, RSS vs heap
3. **Caching strategies** — Write-through, write-behind, cache-aside
4. **Cache invalidation** — TTL, event-driven, versioned keys
5. **Load testing** — Locust, p99 latency, saturation point
