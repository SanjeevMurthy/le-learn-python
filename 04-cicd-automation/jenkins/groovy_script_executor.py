"""
groovy_script_executor.py

Execute Groovy scripts on Jenkins via the Script Console API.

Prerequisites:
- requests (pip install requests)
"""

import os
import logging
from typing import Dict, Any

import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _get_auth():
    return HTTPBasicAuth(
        os.environ.get('JENKINS_USER', 'admin'),
        os.environ.get('JENKINS_TOKEN', '')
    )


def _get_base_url():
    return os.environ.get('JENKINS_URL', 'http://localhost:8080')


def execute_groovy(script: str) -> Dict[str, Any]:
    """
    Execute a Groovy script on the Jenkins controller.

    WARNING: Script Console has full access to Jenkins internals.
    Only use with proper RBAC controls.

    Interview Question:
        Q: When would you use the Jenkins Script Console?
        A: 1. Bulk operations (disable/enable jobs, update config)
           2. Debugging (inspect Jenkins internals)
           3. One-time migrations (rename jobs, update credentials)
           4. Jenkins Configuration as Code (JCasC) troubleshooting
           CRITICAL: never expose Script Console to untrusted users.
    """
    url = f'{_get_base_url()}/scriptText'
    response = requests.post(
        url, auth=_get_auth(), data={'script': script}
    )

    if response.status_code == 200:
        logger.info("Groovy script executed successfully")
        return {'status': 'ok', 'output': response.text}
    return {'status': 'error', 'code': response.status_code, 'output': response.text}


# Useful Groovy snippets
SNIPPETS = {
    'list_credentials': '''
import com.cloudbees.plugins.credentials.CredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
def creds = CredentialsProvider.lookupCredentials(
    com.cloudbees.plugins.credentials.common.StandardCredentials,
    Jenkins.instance, null, null
)
creds.each { println "${it.id}: ${it.class.simpleName}" }
''',
    'list_nodes': '''
Jenkins.instance.nodes.each { node ->
    println "${node.displayName}: ${node.numExecutors} executors, " +
        "online=${node.toComputer()?.isOnline()}"
}
''',
    'disable_jobs_by_pattern': '''
def pattern = ~/.*-deprecated.*/
Jenkins.instance.getAllItems(hudson.model.AbstractProject).each { job ->
    if (job.name =~ pattern) {
        job.disabled = true
        job.save()
        println "Disabled: ${job.fullName}"
    }
}
''',
}


if __name__ == "__main__":
    print("Groovy Script Executor — Usage Examples")
    print("""
    # Execute a groovy script
    result = execute_groovy('println Jenkins.instance.numExecutors')

    # Use a built-in snippet
    result = execute_groovy(SNIPPETS['list_nodes'])
    print(result['output'])
    """)
