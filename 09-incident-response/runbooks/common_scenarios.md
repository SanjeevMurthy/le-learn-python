# Common Incident Response Scenarios

## High CPU Usage

1. Identify top processes: `top`, `htop`, `pidstat`
2. Check if it's user or system CPU
3. Profile the process (`perf`, `py-spy`)
4. Common causes: infinite loops, regex backtracking, GC pressure
5. Remediation: kill process, scale horizontally, optimize code

## Memory Leak

1. Check memory trend: `free -m`, Prometheus `node_memory_*`
2. Identify process: `ps aux --sort=-%mem`
3. For Python: `tracemalloc`, `objgraph`
4. For Java: heap dump + MAT
5. Remediation: restart (short-term), fix leak (long-term)

## Disk Space Full

1. Find large files: `du -sh /* | sort -rh | head`
2. Check inodes: `df -i`
3. Common culprits: logs, temp files, Docker images
4. Clean: rotate logs, `docker system prune`, clear /tmp
5. Prevention: monitoring + alerts at 80% threshold

## Network Issues

1. Check connectivity: `ping`, `traceroute`, `mtr`
2. DNS resolution: `dig`, `nslookup`
3. Port connectivity: `telnet`, `nc -zv`
4. TLS issues: `openssl s_client`
5. Packet analysis: `tcpdump`, Wireshark

## Service Outage

1. Check service status: `systemctl status`, K8s pod status
2. Review recent deployments (was anything just released?)
3. Check dependencies (database, cache, external APIs)
4. Review logs for errors
5. Communicate: update status page, notify stakeholders
