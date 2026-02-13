"""
custom_exceptions.py

Custom exception hierarchy for DevOps/SRE operations.

Interview Topics:
- Why create custom exceptions instead of using built-in ones?
- How to design a clean exception hierarchy?
- Exception handling best practices in production

Production Use Cases:
- Distinguishing between transient and permanent failures
- Adding context to exceptions (instance ID, region, operation name)
- Enabling targeted except blocks for different failure modes
- Structured error reporting with error codes

Prerequisites:
- No external packages needed (stdlib only)
"""

import logging
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Base Exception
# ============================================================

class DevOpsError(Exception):
    """
    Base exception for all DevOps/SRE operations.

    All custom exceptions inherit from this, enabling a single
    'except DevOpsError' to catch any toolkit-related error.

    Attributes:
        message: Human-readable error description
        error_code: Machine-readable error code for monitoring/alerting
        context: Additional context (instance ID, region, etc.)
        retryable: Whether this error is transient and can be retried

    Interview Question:
        Q: Why create a custom exception hierarchy?
        A: 1. Distinguishes our errors from system/library errors
           2. Adds domain-specific context (instance ID, region)
           3. Enables targeted error handling (retry transient, alert permanent)
           4. Machine-readable error codes for monitoring dashboards
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retryable: bool = False
    ):
        # Call the base Exception constructor with the message
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "DEVOPS_ERROR"
        self.context = context or {}
        self.retryable = retryable

    def __str__(self) -> str:
        """Format error with code and context for readable logging."""
        parts = [f"[{self.error_code}] {self.message}"]
        if self.context:
            ctx_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"Context: {ctx_str}")
        if self.retryable:
            parts.append("(retryable)")
        return " | ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for structured logging / API responses."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context,
            "retryable": self.retryable,
            "type": type(self).__name__
        }


# ============================================================
# Cloud Provider Exceptions
# ============================================================

class CloudProviderError(DevOpsError):
    """Base exception for cloud provider operations (AWS, GCP, Azure)."""

    def __init__(
        self,
        message: str,
        provider: str = "unknown",
        region: str = "unknown",
        **kwargs
    ):
        # Add cloud-specific context
        context = kwargs.pop("context", {})
        context.update({"provider": provider, "region": region})
        super().__init__(message, context=context, **kwargs)
        self.provider = provider
        self.region = region


class ResourceNotFoundError(CloudProviderError):
    """Resource (instance, bucket, pod) does not exist."""

    def __init__(self, resource_type: str, resource_id: str, **kwargs):
        message = f"{resource_type} '{resource_id}' not found"
        super().__init__(
            message,
            error_code="RESOURCE_NOT_FOUND",
            retryable=False,
            **kwargs
        )
        self.resource_type = resource_type
        self.resource_id = resource_id


class ResourceLimitError(CloudProviderError):
    """Cloud resource limit/quota exceeded."""

    def __init__(self, resource_type: str, limit: int, current: int, **kwargs):
        message = (
            f"{resource_type} limit exceeded: "
            f"{current}/{limit} used"
        )
        super().__init__(
            message,
            error_code="RESOURCE_LIMIT_EXCEEDED",
            retryable=False,
            **kwargs
        )


class AuthenticationError(CloudProviderError):
    """Authentication or authorization failure."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message,
            error_code="AUTH_FAILED",
            retryable=False,
            **kwargs
        )


class RateLimitError(CloudProviderError):
    """API rate limit exceeded — retryable with backoff."""

    def __init__(self, service: str, retry_after: Optional[float] = None, **kwargs):
        message = f"Rate limit exceeded for {service}"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        super().__init__(
            message,
            error_code="RATE_LIMIT",
            retryable=True,  # Rate limits are transient
            **kwargs
        )
        self.retry_after = retry_after


# ============================================================
# Kubernetes Exceptions
# ============================================================

class KubernetesError(DevOpsError):
    """Base exception for Kubernetes operations."""

    def __init__(
        self,
        message: str,
        namespace: str = "default",
        **kwargs
    ):
        context = kwargs.pop("context", {})
        context["namespace"] = namespace
        super().__init__(message, context=context, **kwargs)
        self.namespace = namespace


class PodNotFoundError(KubernetesError):
    """Pod does not exist in the specified namespace."""

    def __init__(self, pod_name: str, namespace: str = "default"):
        super().__init__(
            f"Pod '{pod_name}' not found",
            namespace=namespace,
            error_code="POD_NOT_FOUND",
            retryable=False
        )


class DeploymentFailedError(KubernetesError):
    """Deployment rollout failed."""

    def __init__(self, deployment_name: str, reason: str, namespace: str = "default"):
        super().__init__(
            f"Deployment '{deployment_name}' failed: {reason}",
            namespace=namespace,
            error_code="DEPLOYMENT_FAILED",
            retryable=False
        )


# ============================================================
# CI/CD Exceptions
# ============================================================

class PipelineError(DevOpsError):
    """Base exception for CI/CD pipeline operations."""
    pass


class BuildFailedError(PipelineError):
    """Build or pipeline execution failed."""

    def __init__(self, pipeline_name: str, build_number: int, reason: str = ""):
        super().__init__(
            f"Build #{build_number} of '{pipeline_name}' failed: {reason}",
            error_code="BUILD_FAILED",
            context={"pipeline": pipeline_name, "build_number": build_number},
            retryable=False
        )


class ArtifactNotFoundError(PipelineError):
    """Build artifact not found."""

    def __init__(self, artifact_path: str):
        super().__init__(
            f"Artifact not found: {artifact_path}",
            error_code="ARTIFACT_NOT_FOUND",
            retryable=False
        )


# ============================================================
# Helper Functions
# ============================================================

def handle_exception(error: DevOpsError) -> Dict[str, Any]:
    """
    Central exception handler — log and return structured error info.

    Use this in top-level try/except blocks to ensure consistent
    error reporting across all scripts.

    Args:
        error: Any DevOpsError instance

    Returns:
        Structured error dictionary for API responses or logging
    """
    error_dict = error.to_dict()

    # Use appropriate log level based on retryability
    if error.retryable:
        logger.warning(f"Retryable error: {error}")
    else:
        logger.error(f"Permanent error: {error}")

    return error_dict


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Custom Exceptions — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Cloud provider error with context ----
    print("\n--- Example 1: Cloud Provider Error ---")
    try:
        raise ResourceNotFoundError(
            resource_type="EC2 Instance",
            resource_id="i-1234567890abcdef0",
            provider="aws",
            region="us-east-1"
        )
    except DevOpsError as e:
        result = handle_exception(e)
        print(f"  Error dict: {result}")
        print(f"  Retryable: {e.retryable}")

    # ---- Example 2: Rate limit (retryable) ----
    print("\n--- Example 2: Rate Limit Error ---")
    try:
        raise RateLimitError(
            service="EC2 DescribeInstances",
            retry_after=5.0,
            provider="aws",
            region="us-west-2"
        )
    except DevOpsError as e:
        result = handle_exception(e)
        print(f"  Error dict: {result}")
        print(f"  Retryable: {e.retryable}")

    # ---- Example 3: Kubernetes error ----
    print("\n--- Example 3: Kubernetes Error ---")
    try:
        raise DeploymentFailedError(
            deployment_name="api-server",
            reason="ImagePullBackOff",
            namespace="production"
        )
    except KubernetesError as e:
        result = handle_exception(e)
        print(f"  Error dict: {result}")

    # ---- Example 4: Catching by hierarchy ----
    print("\n--- Example 4: Exception Hierarchy ---")
    errors = [
        ResourceNotFoundError("EC2 Instance", "i-123", provider="aws", region="us-east-1"),
        RateLimitError("S3", retry_after=3.0, provider="aws", region="us-east-1"),
        PodNotFoundError("my-pod", "default"),
        BuildFailedError("deploy-pipeline", 42, "Test failures"),
    ]

    for error in errors:
        # All caught by the base DevOpsError
        print(f"  {type(error).__name__}: retryable={error.retryable}, code={error.error_code}")
