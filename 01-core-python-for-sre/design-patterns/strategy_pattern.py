"""
strategy_pattern.py

Strategy pattern for interchangeable algorithms in DevOps operations.

Interview Topics:
- Strategy vs if/elif chains
- Open/Closed principle
- Runtime algorithm selection

Production Use Cases:
- Multiple deployment strategies (blue-green, canary, rolling)
- Different backup strategies per environment
- Configurable alert routing
- Interchangeable cloud provider APIs

Prerequisites:
- No external packages needed (stdlib only)
"""

import logging
import time
from typing import Dict, Any, Callable, List, Optional
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Approach 1: Function-based strategy (Pythonic)
# ============================================================

def deploy_rolling(service_name: str, version: str, **kwargs) -> Dict[str, Any]:
    """
    Rolling deployment strategy.

    Gradually replaces old instances with new ones, one at a time.

    Interview Question:
        Q: Compare rolling, blue-green, and canary deployment strategies.
        A: Rolling: gradual replacement, no extra infrastructure,
              risk of mixed versions during deploy.
           Blue-Green: two identical environments, instant switchover,
              fast rollback, but double the infrastructure cost.
           Canary: send small % of traffic to new version first,
              validate metrics, then gradually increase.
              Low risk but complex routing needed.
    """
    print(f"  🔄 Rolling deploy: {service_name} → v{version}")
    print(f"     Replacing instances one by one...")
    replicas = kwargs.get('replicas', 3)
    for i in range(replicas):
        time.sleep(0.05)
        print(f"     Instance {i + 1}/{replicas} updated")
    return {'strategy': 'rolling', 'service': service_name, 'version': version, 'status': 'success'}


def deploy_blue_green(service_name: str, version: str, **kwargs) -> Dict[str, Any]:
    """Blue-green deployment: spin up new environment, switch traffic."""
    print(f"  🔵🟢 Blue-Green deploy: {service_name} → v{version}")
    print(f"     Spinning up green environment...")
    time.sleep(0.05)
    print(f"     Running health checks on green...")
    time.sleep(0.05)
    print(f"     Switching traffic from blue to green")
    return {'strategy': 'blue-green', 'service': service_name, 'version': version, 'status': 'success'}


def deploy_canary(service_name: str, version: str, **kwargs) -> Dict[str, Any]:
    """Canary deployment: route small % of traffic to new version."""
    canary_percent = kwargs.get('canary_percent', 10)
    print(f"  🐤 Canary deploy: {service_name} → v{version}")
    print(f"     Routing {canary_percent}% traffic to canary...")
    time.sleep(0.05)
    print(f"     Monitoring error rates...")
    time.sleep(0.05)
    print(f"     Canary healthy - promoting to 100%")
    return {'strategy': 'canary', 'service': service_name, 'version': version, 'status': 'success'}


# Strategy registry
_deploy_strategies: Dict[str, Callable] = {
    'rolling': deploy_rolling,
    'blue-green': deploy_blue_green,
    'canary': deploy_canary,
}


def deploy(
    service_name: str,
    version: str,
    strategy: str = 'rolling',
    **kwargs
) -> Dict[str, Any]:
    """
    Deploy a service using the specified strategy.

    The strategy is selected at runtime, allowing the same deploy
    function to use different algorithms based on configuration.

    Args:
        service_name: Name of the service
        version: Version to deploy
        strategy: Deployment strategy name
        **kwargs: Strategy-specific parameters

    Returns:
        Deployment result
    """
    if strategy not in _deploy_strategies:
        raise ValueError(
            f"Unknown strategy: {strategy}. "
            f"Available: {list(_deploy_strategies.keys())}"
        )

    strategy_func = _deploy_strategies[strategy]
    logger.info(f"Deploying {service_name} v{version} with '{strategy}' strategy")

    start = time.time()
    result = strategy_func(service_name, version, **kwargs)
    result['duration'] = round(time.time() - start, 3)

    return result


def register_deploy_strategy(name: str, func: Callable) -> None:
    """Register a custom deployment strategy."""
    _deploy_strategies[name] = func
    logger.info(f"Registered deployment strategy: {name}")


# ============================================================
# Approach 2: Backup strategies (another real-world example)
# ============================================================

def backup_full(resource: str, destination: str) -> Dict[str, Any]:
    """Full backup — copies everything."""
    return {'type': 'full', 'resource': resource, 'destination': destination, 'size_estimate': 'large'}


def backup_incremental(resource: str, destination: str) -> Dict[str, Any]:
    """Incremental backup — only changes since last backup."""
    return {'type': 'incremental', 'resource': resource, 'destination': destination, 'size_estimate': 'small'}


def backup_snapshot(resource: str, destination: str) -> Dict[str, Any]:
    """Snapshot backup — point-in-time snapshot."""
    return {'type': 'snapshot', 'resource': resource, 'destination': destination, 'size_estimate': 'varies'}


_backup_strategies = {
    'full': backup_full,
    'incremental': backup_incremental,
    'snapshot': backup_snapshot,
}


def create_backup(
    resource: str,
    destination: str,
    strategy: str = 'incremental'
) -> Dict[str, Any]:
    """Create backup using the specified strategy."""
    if strategy not in _backup_strategies:
        raise ValueError(f"Unknown backup strategy: {strategy}")
    return _backup_strategies[strategy](resource, destination)


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Strategy Pattern — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Deployment strategies ----
    print("\n--- Example 1: Deployment Strategies ---")
    for strategy in ['rolling', 'blue-green', 'canary']:
        print(f"\n  Strategy: {strategy}")
        result = deploy('api-service', '2.1.0', strategy=strategy, replicas=3, canary_percent=5)
        print(f"  Result: {result['status']} ({result['duration']}s)")

    # ---- Example 2: Custom strategy ----
    print("\n--- Example 2: Custom Strategy ---")

    def deploy_recreate(service_name, version, **kwargs):
        """Recreate: tear down all, then bring up all (has downtime)."""
        print(f"  ⚠️ Recreate: {service_name} → v{version} (downtime expected)")
        return {'strategy': 'recreate', 'service': service_name, 'version': version, 'status': 'success'}

    register_deploy_strategy('recreate', deploy_recreate)
    result = deploy('batch-worker', '1.5.0', strategy='recreate')

    # ---- Example 3: Backup strategies ----
    print("\n--- Example 3: Backup Strategies ---")
    for strategy in ['full', 'incremental', 'snapshot']:
        backup = create_backup('production-db', 's3://backups/', strategy=strategy)
        print(f"  {strategy}: size={backup['size_estimate']}")
