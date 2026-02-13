"""
factory_pattern.py

Factory pattern for creating cloud provider clients dynamically.

Interview Topics:
- Factory pattern vs direct instantiation
- How to write provider-agnostic code
- Open/Closed principle in practice

Production Use Cases:
- Multi-cloud automation (AWS/GCP/Azure with same interface)
- Environment-specific configuration (dev/staging/prod)
- Plugin systems for extensible tools

Prerequisites:
- No external packages needed (stdlib only)
"""

import logging
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Approach 1: Function-based factory (simpler)
# ============================================================

def create_cloud_client(
    provider: str,
    region: str = "us-east-1",
    **kwargs
) -> Dict[str, Any]:
    """
    Factory function that creates a cloud provider client config.

    Instead of hardcoding 'if provider == aws' everywhere,
    centralize the creation logic in one factory.

    Args:
        provider: Cloud provider name ('aws', 'gcp', 'azure')
        region: Region for the client
        **kwargs: Provider-specific configuration

    Returns:
        Client configuration dictionary

    Interview Question:
        Q: What is the Factory pattern and when would you use it?
        A: Factory encapsulates object creation logic, decoupling
           the caller from specific implementations. Use when:
           1. Object creation is complex (many parameters, validation)
           2. You need to support multiple implementations (AWS/GCP/Azure)
           3. You want to swap implementations without changing callers
           4. Testing — inject mock factories for unit tests
    """
    factories = {
        'aws': _create_aws_client,
        'gcp': _create_gcp_client,
        'azure': _create_azure_client,
    }

    provider_lower = provider.lower()
    if provider_lower not in factories:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {list(factories.keys())}"
        )

    client = factories[provider_lower](region=region, **kwargs)
    logger.info(f"Created {provider} client for region {region}")
    return client


def _create_aws_client(region: str, **kwargs) -> Dict[str, Any]:
    """Create AWS client configuration."""
    return {
        'provider': 'aws',
        'region': region,
        'service_endpoint': f'https://ec2.{region}.amazonaws.com',
        'auth_method': kwargs.get('auth_method', 'iam_role'),
        'sdk': 'boto3',
    }


def _create_gcp_client(region: str, **kwargs) -> Dict[str, Any]:
    """Create GCP client configuration."""
    return {
        'provider': 'gcp',
        'region': region,
        'project_id': kwargs.get('project_id', 'default-project'),
        'service_endpoint': f'https://compute.googleapis.com',
        'auth_method': kwargs.get('auth_method', 'service_account'),
        'sdk': 'google-cloud-compute',
    }


def _create_azure_client(region: str, **kwargs) -> Dict[str, Any]:
    """Create Azure client configuration."""
    return {
        'provider': 'azure',
        'region': region,
        'subscription_id': kwargs.get('subscription_id', ''),
        'service_endpoint': f'https://management.azure.com',
        'auth_method': kwargs.get('auth_method', 'managed_identity'),
        'sdk': 'azure-mgmt-compute',
    }


# ============================================================
# Approach 2: Registry-based factory (extensible)
# ============================================================

# Global registry of notification handlers
_notification_registry: Dict[str, Callable] = {}


def register_notification_handler(channel: str) -> Callable:
    """
    Decorator to register a notification handler.

    This allows adding new notification types without modifying
    the dispatch logic — adhering to the Open/Closed Principle.

    Example:
        @register_notification_handler('slack')
        def send_slack(message, **kwargs):
            ...
    """
    def decorator(func: Callable) -> Callable:
        _notification_registry[channel] = func
        logger.info(f"Registered notification handler: {channel}")
        return func
    return decorator


def send_notification(channel: str, message: str, **kwargs) -> bool:
    """
    Send a notification using the registered handler for the channel.

    Args:
        channel: Notification channel ('slack', 'email', 'pagerduty')
        message: Message to send
        **kwargs: Channel-specific parameters

    Returns:
        True if sent successfully
    """
    if channel not in _notification_registry:
        logger.error(f"No handler registered for channel: {channel}")
        return False

    handler = _notification_registry[channel]
    return handler(message, **kwargs)


# Register some notification handlers
@register_notification_handler('slack')
def _send_slack(message: str, **kwargs) -> bool:
    """Send notification via Slack webhook."""
    slack_channel = kwargs.get('slack_channel', '#alerts')
    logger.info(f"[Slack → {slack_channel}] {message}")
    return True


@register_notification_handler('email')
def _send_email(message: str, **kwargs) -> bool:
    """Send notification via email."""
    to = kwargs.get('to', 'team@example.com')
    logger.info(f"[Email → {to}] {message}")
    return True


@register_notification_handler('pagerduty')
def _send_pagerduty(message: str, **kwargs) -> bool:
    """Create PagerDuty incident."""
    severity = kwargs.get('severity', 'warning')
    logger.info(f"[PagerDuty → {severity}] {message}")
    return True


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Factory Pattern — Usage Examples")
    print("=" * 60)

    # ---- Example 1: Cloud client factory ----
    print("\n--- Example 1: Cloud Client Factory ---")
    for provider in ['aws', 'gcp', 'azure']:
        client = create_cloud_client(provider, region='us-east-1')
        print(f"  {provider}: endpoint={client['service_endpoint']}, sdk={client['sdk']}")

    # ---- Example 2: Registry-based notifications ----
    print("\n--- Example 2: Notification Factory ---")
    send_notification('slack', 'Deployment completed', slack_channel='#deploys')
    send_notification('email', 'Daily report ready', to='admin@company.com')
    send_notification('pagerduty', 'High error rate detected', severity='critical')

    # Try unknown channel
    result = send_notification('sms', 'Test message')
    print(f"  Unknown channel result: {result}")

    # ---- Example 3: List registered handlers ----
    print("\n--- Example 3: Registered Handlers ---")
    for channel in _notification_registry:
        print(f"  {channel}: {_notification_registry[channel].__name__}")
