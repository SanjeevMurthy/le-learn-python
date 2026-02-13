"""
api_design_patterns.py

API design patterns for DevOps/SRE interviews.
"""

import uuid
import time
import logging
from typing import Dict, Any, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def paginated_response(
    items: List[Any],
    page: int = 1,
    page_size: int = 20,
    base_url: str = '/api/items'
) -> Dict[str, Any]:
    """
    Create a paginated API response.

    Interview Question:
        Q: How do you design a REST API for a monitoring dashboard?
        A: Resources: /metrics, /alerts, /dashboards, /incidents.
           Pagination: cursor-based for real-time data (not offset).
           Filtering: query params (?status=firing&severity=critical).
           Versioning: /v1/ or Accept header.
           Rate limiting: per-user, per-endpoint.
           Idempotency: POST with Idempotency-Key header.
    """
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]
    total = len(items)
    total_pages = (total + page_size - 1) // page_size

    response = {
        'data': page_items,
        'pagination': {
            'page': page,
            'page_size': page_size,
            'total_items': total,
            'total_pages': total_pages,
        },
        'links': {},
    }

    if page < total_pages:
        response['links']['next'] = f'{base_url}?page={page + 1}&page_size={page_size}'
    if page > 1:
        response['links']['prev'] = f'{base_url}?page={page - 1}&page_size={page_size}'

    return response


def idempotent_request(
    idempotency_key: str,
    handler,
    cache: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Idempotent request handling.

    Interview Question:
        Q: What is idempotency and why does it matter?
        A: Idempotent: same request repeated → same result.
           GET, PUT, DELETE are naturally idempotent.
           POST is NOT idempotent → use Idempotency-Key header.
           Implementation: store result keyed by idempotency key,
           return cached result on duplicate request.
           Critical for: payment processing, resource creation,
           retry-safe operations.
    """
    if idempotency_key in cache:
        logger.info(f"Returning cached result for key={idempotency_key}")
        return cache[idempotency_key]

    result = handler()
    cache[idempotency_key] = result
    return result


def health_check_endpoint() -> Dict[str, Any]:
    """Standard health check response format."""
    return {
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': time.time(),
        'checks': {
            'database': {'status': 'up', 'latency_ms': 2},
            'cache': {'status': 'up', 'latency_ms': 1},
            'external_api': {'status': 'up', 'latency_ms': 45},
        }
    }


if __name__ == "__main__":
    # Pagination demo
    items = list(range(50))
    page = paginated_response(items, page=2, page_size=10)
    print(f"  Page 2: {page['data']}")
    print(f"  Total: {page['pagination']['total_items']}")
