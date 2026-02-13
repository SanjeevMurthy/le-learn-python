"""
auto_remediation.py

Automated incident remediation framework.

Prerequisites:
- psutil (pip install psutil)
"""

import logging
import time
from typing import Dict, Any, Callable, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def auto_remediate(
    check_fn: Callable[[], bool],
    remediate_fn: Callable[[], Dict[str, Any]],
    name: str,
    max_attempts: int = 3,
    cooldown: int = 30
) -> Dict[str, Any]:
    """
    Generic auto-remediation loop.

    Interview Question:
        Q: What are the risks of auto-remediation?
        A: 1. Masking root cause (auto-restart hides bugs)
           2. Cascading failures (restarting causes thundering herd)
           3. Infinite loop (fix triggers same alert)
           4. Data loss (killing process with unsaved state)
           Best practices: limit attempts, add cooldown,
           alert on repeated remediation, log everything,
           human approval for destructive actions.
    """
    for attempt in range(1, max_attempts + 1):
        if not check_fn():
            logger.info(f"[{name}] Check passed — no remediation needed")
            return {'name': name, 'status': 'healthy', 'attempts': attempt - 1}

        logger.warning(f"[{name}] Attempt {attempt}/{max_attempts} — remediating")
        result = remediate_fn()

        time.sleep(cooldown)

        if not check_fn():
            logger.info(f"[{name}] Remediation successful after {attempt} attempt(s)")
            return {'name': name, 'status': 'remediated', 'attempts': attempt, 'result': result}

    logger.error(f"[{name}] Remediation failed after {max_attempts} attempts — escalating")
    return {'name': name, 'status': 'escalate', 'attempts': max_attempts}


def check_high_memory(threshold: float = 90.0) -> bool:
    """Check if memory usage exceeds threshold."""
    import psutil
    return psutil.virtual_memory().percent > threshold


def check_high_cpu(threshold: float = 90.0) -> bool:
    """Check if CPU usage exceeds threshold."""
    import psutil
    return psutil.cpu_percent(interval=1) > threshold


if __name__ == "__main__":
    print("Auto-Remediation — Usage Examples")
    print("""
    result = auto_remediate(
        check_fn=lambda: check_high_memory(90),
        remediate_fn=lambda: {'action': 'cleared cache'},
        name='high-memory',
        max_attempts=3,
        cooldown=10
    )
    """)
