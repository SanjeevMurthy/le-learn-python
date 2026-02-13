"""
context_logging.py

Contextual logging with correlation IDs for distributed tracing.

Interview Topics:
- Distributed tracing in microservices
- Context propagation across service boundaries
- ContextVar vs threading.local

Production Use Cases:
- Tracing requests across API gateway → service → database
- Debugging production issues by filtering logs by request ID
- Performance monitoring per-request
- User journey tracking

Prerequisites:
- No external packages needed (stdlib only)
"""

import logging
import uuid
import time
import functools
from typing import Any, Callable, Optional, Dict
from contextvars import ContextVar, Token

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ContextVars for request tracking — thread-safe and async-compatible
_request_id: ContextVar[str] = ContextVar('request_id', default='no-request')
_user_id: ContextVar[str] = ContextVar('user_id', default='anonymous')
_operation: ContextVar[str] = ContextVar('operation', default='')


class ContextLogger:
    """
    Logger wrapper that automatically includes context fields in every message.

    Instead of passing request_id, user_id, etc. to every log call,
    set them once per request and they appear in all subsequent logs.

    Interview Question:
        Q: How do you implement distributed tracing without a tracing framework?
        A: Use correlation IDs. Generate a unique ID at the entry point,
           store in ContextVar, include in all log entries, pass in HTTP
           headers to downstream services. This gives you basic tracing
           without Jaeger/Zipkin infrastructure.
    """

    def __init__(self, name: str = __name__):
        self._logger = logging.getLogger(name)

    def _format_message(self, message: str) -> str:
        """Prepend context info to the log message."""
        ctx_parts = []
        req_id = _request_id.get()
        if req_id != 'no-request':
            ctx_parts.append(f"req={req_id}")
        user = _user_id.get()
        if user != 'anonymous':
            ctx_parts.append(f"user={user}")
        operation = _operation.get()
        if operation:
            ctx_parts.append(f"op={operation}")

        prefix = f"[{' '.join(ctx_parts)}] " if ctx_parts else ""
        return f"{prefix}{message}"

    def info(self, message: str, **kwargs) -> None:
        self._logger.info(self._format_message(message), **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        self._logger.warning(self._format_message(message), **kwargs)

    def error(self, message: str, **kwargs) -> None:
        self._logger.error(self._format_message(message), **kwargs)

    def debug(self, message: str, **kwargs) -> None:
        self._logger.debug(self._format_message(message), **kwargs)


def set_request_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    operation: Optional[str] = None
) -> Dict[str, Token]:
    """
    Set context for the current request/operation.

    Returns tokens that can be used to reset context when done.

    Args:
        request_id: Unique request identifier
        user_id: User performing the action
        operation: Name of the current operation

    Returns:
        Dictionary of context tokens for cleanup
    """
    tokens = {}
    if request_id:
        tokens['request_id'] = _request_id.set(request_id)
    if user_id:
        tokens['user_id'] = _user_id.set(user_id)
    if operation:
        tokens['operation'] = _operation.set(operation)
    return tokens


def clear_request_context(tokens: Dict[str, Token]) -> None:
    """Reset context using tokens from set_request_context."""
    if 'request_id' in tokens:
        _request_id.reset(tokens['request_id'])
    if 'user_id' in tokens:
        _user_id.reset(tokens['user_id'])
    if 'operation' in tokens:
        _operation.reset(tokens['operation'])


def with_logging_context(
    operation: Optional[str] = None,
    log_args: bool = False,
    log_result: bool = False,
    log_timing: bool = True
) -> Callable:
    """
    Decorator that automatically sets logging context and logs timing.

    Args:
        operation: Operation name (defaults to function name)
        log_args: Whether to log function arguments
        log_result: Whether to log the return value
        log_timing: Whether to log execution duration

    Returns:
        Decorated function

    Example:
        @with_logging_context(operation="stop_instances", log_timing=True)
        def stop_idle_instances(region: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            op_name = operation or func.__name__
            ctx_logger = ContextLogger(func.__module__)

            # Set operation context
            tokens = set_request_context(operation=op_name)
            start_time = time.time()

            # Optionally log arguments
            if log_args:
                ctx_logger.info(f"Started with args={args}, kwargs={kwargs}")
            else:
                ctx_logger.info("Started")

            try:
                result = func(*args, **kwargs)

                # Log timing
                elapsed = time.time() - start_time
                if log_timing:
                    ctx_logger.info(f"Completed in {elapsed:.3f}s")
                if log_result:
                    ctx_logger.info(f"Result: {result}")

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                ctx_logger.error(f"Failed after {elapsed:.3f}s: {e}")
                raise

            finally:
                clear_request_context(tokens)

        return wrapper
    return decorator


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Context Logging — Usage Examples")
    print("=" * 60)

    ctx_log = ContextLogger("example")

    # ---- Example 1: Manual context setting ----
    print("\n--- Example 1: Manual Context ---")
    tokens = set_request_context(
        request_id="req-abc123",
        user_id="admin@company.com",
        operation="deploy"
    )

    ctx_log.info("Deployment started")
    ctx_log.info("Pulling Docker image")
    ctx_log.warning("Image pull took 15s (slow)")
    ctx_log.info("Deployment completed")

    clear_request_context(tokens)

    # ---- Example 2: Decorator-based context ----
    print("\n--- Example 2: Decorator Context ---")

    # Set request-level context
    tokens = set_request_context(
        request_id="req-def456",
        user_id="sre-bot"
    )

    @with_logging_context(operation="cleanup_snapshots", log_timing=True)
    def cleanup_old_snapshots(region: str, days: int = 30) -> int:
        """Simulate cleaning up old snapshots."""
        time.sleep(0.1)  # Simulate work
        return 5  # Number of snapshots deleted

    deleted = cleanup_old_snapshots("us-east-1", days=7)
    print(f"  Deleted {deleted} snapshots")

    clear_request_context(tokens)

    # ---- Example 3: Nested operations ----
    print("\n--- Example 3: Nested Operations ---")
    tokens = set_request_context(request_id="req-ghi789")

    ctx_log.info("Starting pipeline")

    inner_tokens = set_request_context(operation="build")
    ctx_log.info("Building artifact")
    clear_request_context(inner_tokens)

    inner_tokens = set_request_context(operation="test")
    ctx_log.info("Running tests")
    clear_request_context(inner_tokens)

    inner_tokens = set_request_context(operation="deploy")
    ctx_log.info("Deploying to staging")
    clear_request_context(inner_tokens)

    clear_request_context(tokens)
