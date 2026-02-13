"""
elasticsearch_client.py

Elasticsearch client for log storage and querying.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_base_url():
    return os.environ.get('ELASTICSEARCH_URL', 'http://localhost:9200')


def search_logs(
    index: str = 'logs-*',
    query: str = '*',
    size: int = 100,
    time_range: str = 'now-1h'
) -> List[Dict[str, Any]]:
    """
    Search logs in Elasticsearch.

    Interview Question:
        Q: Describe the EFK stack.
        A: Elasticsearch: distributed search/analytics engine, stores logs.
           Fluentd/Fluent Bit: log collection and forwarding (DaemonSet).
           Kibana: visualization and exploration.
           Alternative: ELK (Logstash instead of Fluentd).
           Modern alternative: Grafana Loki (log aggregation without
           indexing content, just labels — much cheaper storage).
    """
    url = f'{_get_base_url()}/{index}/_search'
    body = {
        'size': size,
        'query': {
            'bool': {
                'must': [{'query_string': {'query': query}}],
                'filter': [{'range': {'@timestamp': {'gte': time_range}}}],
            }
        },
        'sort': [{'@timestamp': {'order': 'desc'}}],
    }

    response = requests.post(url, json=body, headers={'Content-Type': 'application/json'})
    response.raise_for_status()
    data = response.json()

    hits = []
    for hit in data.get('hits', {}).get('hits', []):
        source = hit.get('_source', {})
        hits.append({
            'timestamp': source.get('@timestamp', ''),
            'level': source.get('level', ''),
            'message': source.get('message', ''),
            'service': source.get('service', ''),
            'index': hit.get('_index', ''),
        })

    logger.info(f"Found {len(hits)} log entries")
    return hits


def index_document(
    index: str,
    document: Dict[str, Any]
) -> Dict[str, Any]:
    """Index a log document."""
    if '@timestamp' not in document:
        document['@timestamp'] = datetime.now(timezone.utc).isoformat()

    url = f'{_get_base_url()}/{index}/_doc'
    response = requests.post(url, json=document, headers={'Content-Type': 'application/json'})
    return {'status': 'created' if response.status_code == 201 else 'error'}


if __name__ == "__main__":
    print("Elasticsearch Client — Usage Examples")
    print("""
    logs = search_logs(query='level:ERROR AND service:api-gateway')
    for log in logs:
        print(f"  [{log['level']}] {log['service']}: {log['message']}")
    """)
