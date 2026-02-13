"""
singleton_pattern.py

Singleton pattern for shared resources in DevOps tools.

Interview Topics:
- When is Singleton appropriate in DevOps?
- Thread-safe Singleton implementation
- Singleton vs module-level globals

Production Use Cases:
- Configuration manager (one source of truth)
- Database connection pool (shared resource)
- API client with rate limiting state
- Logging configuration

Prerequisites:
- No external packages needed (stdlib only)
"""

import logging
import threading
from typing import Any, Dict, Optional

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Approach 1: Module-level function (Pythonic Singleton)
# ============================================================

_config_instance: Optional[Dict] = None
_config_lock = threading.Lock()


def get_config(config_path: Optional[str] = None) -> Dict:
    """
    Get the global configuration (creates on first call, reuses after).

    This is the most Pythonic way to implement a singleton — just use
    module-level state. Python modules are imported once and cached.

    Args:
        config_path: Path to config file (only used on first call)

    Returns:
        Configuration dictionary (always the same instance)

    Interview Question:
        Q: What is the Singleton pattern and when would you use it?
        A: Singleton ensures only one instance of a class exists.
           In DevOps, use it for: config managers (one source of truth),
           connection pools (shared resource), rate limiters (global state).
           In Python, prefer module-level functions + globals over
           class-based Singleton — it's simpler and more Pythonic.
    """
    global _config_instance

    if _config_instance is None:
        with _config_lock:
            # Double-checked locking — check again inside the lock
            # to prevent race condition where two threads both see None
            if _config_instance is None:
                logger.info("Creating configuration singleton")
                _config_instance = _load_config(config_path)

    return _config_instance


def _load_config(config_path: Optional[str] = None) -> Dict:
    """Load configuration from file or defaults."""
    # In production, this would read from a YAML/JSON file
    defaults = {
        'app_name': 'devops-toolkit',
        'log_level': 'INFO',
        'max_retries': 3,
        'timeout_seconds': 30,
        'regions': ['us-east-1', 'us-west-2', 'eu-west-1'],
        'feature_flags': {
            'enable_auto_remediation': True,
            'enable_cost_alerts': True,
        }
    }

    if config_path:
        try:
            import json
            with open(config_path, 'r') as f:
                file_config = json.load(f)
            defaults.update(file_config)
            logger.info(f"Loaded config from {config_path}")
        except Exception as e:
            logger.warning(f"Could not load {config_path}: {e}. Using defaults.")

    return defaults


def reset_config() -> None:
    """Reset the singleton (useful for testing)."""
    global _config_instance
    with _config_lock:
        _config_instance = None
        logger.info("Configuration singleton reset")


# ============================================================
# Approach 2: Class-based Singleton (for stateful resources)
# ============================================================

class ConnectionPool:
    """
    Thread-safe connection pool singleton.

    Uses __new__ to ensure only one instance is created.

    Interview Question:
        Q: How do you implement a thread-safe Singleton?
        A: 1. Use a lock to protect instance creation
           2. Double-checked locking for performance (check before and after lock)
           3. In Python, __new__ runs before __init__ — override it
           4. Alternative: use a module-level variable (simpler and sufficient)
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, pool_size: int = 10, host: str = "localhost"):
        if self._initialized:
            return
        self._pool_size = pool_size
        self._host = host
        self._connections: list = []
        self._initialized = True
        logger.info(f"ConnectionPool created: host={host}, size={pool_size}")

    @property
    def pool_size(self) -> int:
        return self._pool_size

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    def get_connection(self) -> Dict[str, Any]:
        """Get a connection from the pool."""
        if len(self._connections) < self._pool_size:
            conn = {'id': len(self._connections) + 1, 'host': self._host}
            self._connections.append(conn)
            return conn
        raise RuntimeError("Connection pool exhausted")

    def release_connection(self, conn: Dict[str, Any]) -> None:
        """Return a connection to the pool."""
        if conn in self._connections:
            self._connections.remove(conn)


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Singleton Pattern — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Config singleton ----
    print("\n--- Example 1: Config Singleton ---")
    config1 = get_config()
    config2 = get_config()  # Same instance

    print(f"  Same instance? {config1 is config2}")
    print(f"  App name: {config1['app_name']}")
    print(f"  Regions: {config1['regions']}")

    # ---- Example 2: Connection pool singleton ----
    print("\n--- Example 2: Connection Pool Singleton ---")
    pool1 = ConnectionPool(pool_size=5, host="db.example.com")
    pool2 = ConnectionPool()  # Returns the SAME instance

    print(f"  Same instance? {pool1 is pool2}")
    print(f"  Pool size: {pool1.pool_size}")

    conn = pool1.get_connection()
    print(f"  Got connection: {conn}")
    print(f"  Active connections: {pool1.active_connections}")

    # ---- Example 3: Thread safety proof ----
    print("\n--- Example 3: Thread Safety ---")
    reset_config()
    instances = []

    def get_config_thread():
        instances.append(id(get_config()))

    threads = [threading.Thread(target=get_config_thread) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    unique_ids = set(instances)
    print(f"  10 threads, unique instances: {len(unique_ids)} (should be 1)")
