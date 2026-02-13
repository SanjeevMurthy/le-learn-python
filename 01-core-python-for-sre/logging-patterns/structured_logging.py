"""
structured_logging.py

JSON-structured logging for production systems and log aggregation.

Interview Topics:
- Why structured logging over plain text?
- How to correlate logs across microservices?
- Log levels and when to use each

Production Use Cases:
- Feeding logs into ELK/Splunk/CloudWatch for search and analysis
- Adding correlation IDs for request tracing
- Performance metrics in log entries
- Audit logging for compliance

Prerequisites:
- structlog (pip install structlog)
- python-json-logger (pip install python-json-logger) — optional
"""

import json
import time
import uuid
import logging
import sys
from typing import Any, Dict, Optional
from datetime import datetime
from contextvars import ContextVar

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Context variable for request/correlation ID tracking
# ContextVar is thread-safe and works with asyncio
_correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def setup_json_logging(
    level: int = logging.INFO,
    service_name: str = "devops-toolkit",
    include_timestamp: bool = True,
    output_stream: Any = None
) -> logging.Logger:
    """
    Configure JSON-formatted logging for structured log output.

    JSON logging enables log aggregation tools (ELK, Splunk, CloudWatch Logs)
    to parse and index log fields automatically.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        service_name: Name of the service (added to every log entry)
        include_timestamp: Whether to add ISO-8601 timestamp
        output_stream: Output stream (default: sys.stdout)

    Returns:
        Configured logger instance

    Interview Question:
        Q: Why use structured (JSON) logging instead of plain text?
        A: 1. Machine-parseable — log aggregation tools can index fields
           2. Searchable — query by any field (user_id, request_id, error_code)
           3. Consistent — uniform format across all services
           4. Rich context — attach metadata without format string gymnastics
           5. Alertable — set up alerts on specific field values
    """

    class JsonFormatter(logging.Formatter):
        """Custom formatter that outputs JSON-structured log lines."""

        def format(self, record: logging.LogRecord) -> str:
            # Build the base log entry
            log_entry = {
                'level': record.levelname,
                'message': record.getMessage(),
                'logger': record.name,
                'service': service_name,
            }

            # Add timestamp in ISO-8601 format
            if include_timestamp:
                log_entry['timestamp'] = datetime.utcnow().isoformat() + 'Z'

            # Add correlation ID if set (for request tracing)
            correlation_id = _correlation_id.get()
            if correlation_id:
                log_entry['correlation_id'] = correlation_id

            # Add exception info if present
            if record.exc_info and record.exc_info[0] is not None:
                log_entry['exception'] = {
                    'type': record.exc_info[0].__name__,
                    'message': str(record.exc_info[1]),
                }

            # Add any extra fields passed via logger.info("msg", extra={...})
            if hasattr(record, 'extra_data'):
                log_entry.update(record.extra_data)

            return json.dumps(log_entry)

    # Create and configure the logger
    json_logger = logging.getLogger(f"{service_name}.json")
    json_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    json_logger.handlers = []

    # Add handler with JSON formatter
    handler = logging.StreamHandler(output_stream or sys.stdout)
    handler.setFormatter(JsonFormatter())
    json_logger.addHandler(handler)

    return json_logger


def log_with_context(
    log_func,
    message: str,
    **context_fields
) -> None:
    """
    Log a message with additional context fields.

    This helper attaches extra key-value pairs to the log entry,
    which appear as searchable fields in the JSON output.

    Args:
        log_func: Logger method (e.g., logger.info, logger.error)
        message: Log message
        **context_fields: Additional fields to include in the log entry

    Example:
        log_with_context(
            logger.info, "Instance stopped",
            instance_id="i-123", region="us-east-1", duration_ms=450
        )
    """
    log_func(message, extra={'extra_data': context_fields})


def set_correlation_id(correlation_id: Optional[str] = None) -> str:
    """
    Set a correlation ID for the current context (thread/coroutine).

    Correlation IDs let you trace a single request across multiple
    services in a microservices architecture.

    Args:
        correlation_id: ID to use, or auto-generate UUID if None

    Returns:
        The correlation ID that was set

    Interview Question:
        Q: How do you trace a request across microservices?
        A: Generate a unique correlation ID at the entry point (API gateway),
           pass it via HTTP header (X-Correlation-ID), include it in every
           log entry, pass it to downstream service calls. This lets you
           search all logs from a single user request across all services.
    """
    cid = correlation_id or str(uuid.uuid4())[:8]
    _correlation_id.set(cid)
    return cid


def clear_correlation_id() -> None:
    """Clear the correlation ID for the current context."""
    _correlation_id.set(None)


def create_audit_logger(
    audit_log_file: str = "audit.log",
    service_name: str = "devops-toolkit"
) -> logging.Logger:
    """
    Create a separate audit logger for compliance-sensitive operations.

    Audit logs are kept separate from application logs because:
    1. Different retention policies (often legally required)
    2. Tamper-proof storage requirements
    3. Different access controls (security team access)

    Args:
        audit_log_file: Path to the audit log file
        service_name: Service name for log entries

    Returns:
        Configured audit logger
    """
    audit_logger = logging.getLogger(f"{service_name}.audit")
    audit_logger.setLevel(logging.INFO)
    audit_logger.handlers = []

    handler = logging.FileHandler(audit_log_file)

    class AuditFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': 'AUDIT',
                'message': record.getMessage(),
                'service': service_name,
            }
            if hasattr(record, 'extra_data'):
                entry.update(record.extra_data)
            return json.dumps(entry)

    handler.setFormatter(AuditFormatter())
    audit_logger.addHandler(handler)
    return audit_logger


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Structured Logging — Usage Examples")
    print("=" * 60)

    # ---- Example 1: JSON logging ----
    print("\n--- Example 1: JSON Structured Logging ---")
    json_logger = setup_json_logging(service_name="api-gateway")

    # Set correlation ID for request tracing
    cid = set_correlation_id()
    print(f"  Correlation ID: {cid}")

    # Log with context fields
    log_with_context(
        json_logger.info, "Request received",
        method="GET", path="/api/v1/users", client_ip="10.0.1.50"
    )

    log_with_context(
        json_logger.info, "Database query completed",
        table="users", rows_returned=42, query_time_ms=12.5
    )

    log_with_context(
        json_logger.warning, "Slow response detected",
        endpoint="/api/v1/search", response_time_ms=2500, threshold_ms=1000
    )

    # Log an error with exception
    try:
        result = 1 / 0
    except ZeroDivisionError:
        json_logger.error("Calculation failed", exc_info=True)

    clear_correlation_id()

    # ---- Example 2: Standard formatted output ----
    print("\n--- Example 2: Context-Rich Logging ---")
    print("  (See JSON output above for structured format)")
    print("  Key fields: timestamp, level, message, correlation_id, service")
    print("  Custom fields: method, path, query_time_ms, etc.")
