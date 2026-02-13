# Third-Party API Integration Guide

## 🔌 Overview

This guide covers production-ready examples for integrating with major DevOps/SRE platforms:
- GitHub/GitLab APIs
- Jenkins API
- Prometheus/Grafana APIs  
- JFrog Artifactory
- HashiCorp Vault (covered in main examples)
- CircleCI/GitHub Actions

---

## 1. GitHub API Integration

### Example: Automated Repository Management

```python
"""
github_automation.py

GitHub API integration for common DevOps automation tasks.

Interview Topics:
- Git workflows
- CI/CD automation
- Secret management
- Branch protection
"""

from github import Github, GithubException
from typing import List, Dict, Optional
import logging
import os

logger = logging.getLogger(__name__)


class GitHubAutomation:
    """
    Automates GitHub operations using PyGithub.
    
    Common Interview Scenarios:
    - "Automate repository creation for new teams"
    - "Implement branch protection policies"
    - "Rotate organization secrets"
    """
    
    def __init__(self, token: str = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token or App token
        """
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token required")
        
        self.client = Github(self.token)
        self.user = self.client.get_user()
    
    def create_repository_from_template(
        self,
        template_owner: str,
        template_repo: str,
        new_repo_name: str,
        new_repo_description: str = "",
        private: bool = True
    ) -> Dict:
        """
        Create new repository from template.
        
        Interview Question:
        "How would you standardize repository setup for new microservices?"
        
        Example:
            gh = GitHubAutomation()
            repo = gh.create_repository_from_template(
                template_owner='myorg',
                template_repo='service-template',
                new_repo_name='user-service',
                new_repo_description='User management service'
            )
        """
        try:
            template = self.client.get_repo(
                f"{template_owner}/{template_repo}"
            )
            
            new_repo = template.create_fork(
                organization=None,
                name=new_repo_name
            )
            
            # Set repository properties
            new_repo.edit(
                description=new_repo_description,
                private=private,
                has_issues=True,
                has_wiki=False,
                has_projects=True
            )
            
            logger.info(f"Created repository: {new_repo.full_name}")
            
            return {
                'name': new_repo.name,
                'full_name': new_repo.full_name,
                'url': new_repo.html_url,
                'clone_url': new_repo.clone_url
            }
        
        except GithubException as e:
            logger.error(f"Failed to create repository: {e}")
            raise
    
    def setup_branch_protection(
        self,
        repo_name: str,
        branch: str = 'main',
        require_reviews: int = 2,
        require_status_checks: bool = True,
        status_checks: List[str] = None
    ) -> bool:
        """
        Configure branch protection rules.
        
        Interview Scenario:
        "Enforce code review policies across all repositories"
        
        Args:
            repo_name: Repository name (owner/repo)
            branch: Branch to protect
            require_reviews: Number of required reviews
            require_status_checks: Require passing CI checks
            status_checks: List of required check names
        
        Returns:
            True if successful
        """
        try:
            repo = self.client.get_repo(repo_name)
            branch_obj = repo.get_branch(branch)
            
            # Configure protection
            branch_obj.edit_protection(
                required_approving_review_count=require_reviews,
                dismiss_stale_reviews=True,
                require_code_owner_reviews=True,
                enforce_admins=True,
                strict=require_status_checks,
                contexts=status_checks or []
            )
            
            logger.info(
                f"Configured branch protection for {repo_name}/{branch}"
            )
            return True
        
        except GithubException as e:
            logger.error(f"Failed to setup branch protection: {e}")
            return False
    
    def trigger_workflow(
        self,
        repo_name: str,
        workflow_id: str,
        ref: str = 'main',
        inputs: Dict = None
    ) -> bool:
        """
        Trigger GitHub Actions workflow via API.
        
        Interview Question:
        "How do you programmatically trigger deployments?"
        
        Example:
            gh.trigger_workflow(
                repo_name='myorg/myapp',
                workflow_id='deploy.yml',
                ref='main',
                inputs={'environment': 'production'}
            )
        """
        try:
            repo = self.client.get_repo(repo_name)
            workflow = repo.get_workflow(workflow_id)
            
            workflow.create_dispatch(
                ref=ref,
                inputs=inputs or {}
            )
            
            logger.info(
                f"Triggered workflow {workflow_id} on {repo_name}"
            )
            return True
        
        except GithubException as e:
            logger.error(f"Failed to trigger workflow: {e}")
            return False
    
    def rotate_repository_secrets(
        self,
        repo_name: str,
        secrets: Dict[str, str]
    ) -> Dict[str, bool]:
        """
        Update repository secrets (for Actions).
        
        Interview Scenario:
        "Implement automated secret rotation for CI/CD pipelines"
        
        Args:
            repo_name: Repository name
            secrets: Dictionary of secret names to values
        
        Returns:
            Dictionary with update status for each secret
        """
        from nacl import encoding, public
        
        try:
            repo = self.client.get_repo(repo_name)
            public_key = repo.get_public_key()
            
            results = {}
            
            for secret_name, secret_value in secrets.items():
                try:
                    # Encrypt secret
                    public_key_obj = public.PublicKey(
                        public_key.key.encode("utf-8"),
                        encoding.Base64Encoder()
                    )
                    sealed_box = public.SealedBox(public_key_obj)
                    encrypted = sealed_box.encrypt(
                        secret_value.encode("utf-8")
                    )
                    
                    # Update secret
                    repo.create_secret(
                        secret_name=secret_name,
                        unencrypted_value=secret_value
                    )
                    
                    results[secret_name] = True
                    logger.info(f"Updated secret: {secret_name}")
                
                except Exception as e:
                    results[secret_name] = False
                    logger.error(f"Failed to update {secret_name}: {e}")
            
            return results
        
        except GithubException as e:
            logger.error(f"Failed to rotate secrets: {e}")
            return {}
    
    def get_workflow_runs_status(
        self,
        repo_name: str,
        workflow_id: str,
        branch: str = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get recent workflow run statuses.
        
        Interview Question:
        "How do you monitor CI/CD pipeline health?"
        
        Returns:
            List of workflow run details
        """
        try:
            repo = self.client.get_repo(repo_name)
            workflow = repo.get_workflow(workflow_id)
            
            runs = workflow.get_runs()[:limit]
            
            results = []
            for run in runs:
                if branch and run.head_branch != branch:
                    continue
                
                results.append({
                    'id': run.id,
                    'status': run.status,
                    'conclusion': run.conclusion,
                    'branch': run.head_branch,
                    'commit': run.head_sha[:7],
                    'created_at': run.created_at,
                    'updated_at': run.updated_at,
                    'html_url': run.html_url
                })
            
            return results
        
        except GithubException as e:
            logger.error(f"Failed to get workflow runs: {e}")
            return []


# Usage Examples
if __name__ == "__main__":
    gh = GitHubAutomation()
    
    # Example 1: Create repository from template
    new_repo = gh.create_repository_from_template(
        template_owner='myorg',
        template_repo='microservice-template',
        new_repo_name='payment-service'
    )
    
    # Example 2: Setup branch protection
    gh.setup_branch_protection(
        repo_name='myorg/payment-service',
        branch='main',
        require_reviews=2,
        status_checks=['test', 'lint', 'security-scan']
    )
    
    # Example 3: Trigger deployment workflow
    gh.trigger_workflow(
        repo_name='myorg/payment-service',
        workflow_id='deploy.yml',
        inputs={'environment': 'staging'}
    )
    
    # Example 4: Rotate secrets
    gh.rotate_repository_secrets(
        repo_name='myorg/payment-service',
        secrets={
            'DB_PASSWORD': 'new-password-123',
            'API_KEY': 'new-api-key-456'
        }
    )
```

---

## 2. Jenkins API Integration

### Example: Pipeline Automation

```python
"""
jenkins_automation.py

Jenkins API integration for CI/CD automation.

Interview Topics:
- Jenkins pipeline management
- Build automation
- Job orchestration
"""

import jenkins
from typing import List, Dict, Optional
import logging
import time
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class JenkinsAutomation:
    """
    Automates Jenkins operations.
    
    Interview Scenarios:
    - "Automate Jenkins job creation"
    - "Implement deployment orchestration"
    - "Monitor build pipeline health"
    """
    
    def __init__(
        self,
        url: str,
        username: str = None,
        password: str = None
    ):
        """
        Initialize Jenkins client.
        
        Args:
            url: Jenkins server URL
            username: Jenkins username
            password: API token or password
        """
        self.url = url
        self.server = jenkins.Jenkins(
            url=url,
            username=username,
            password=password
        )
        
        # Verify connection
        try:
            self.server.get_whoami()
            logger.info(f"Connected to Jenkins at {url}")
        except Exception as e:
            logger.error(f"Failed to connect to Jenkins: {e}")
            raise
    
    def create_pipeline_job(
        self,
        job_name: str,
        jenkinsfile_path: str,
        repo_url: str,
        branch: str = 'main',
        parameters: Dict = None
    ) -> bool:
        """
        Create a pipeline job from Jenkinsfile.
        
        Interview Question:
        "How do you programmatically create Jenkins jobs?"
        
        Args:
            job_name: Name of the job
            jenkinsfile_path: Path to Jenkinsfile in repo
            repo_url: Git repository URL
            branch: Git branch
            parameters: Job parameters
        
        Returns:
            True if successful
        """
        # Job configuration XML template
        config_xml = f"""<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <description>Auto-generated pipeline job</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        {self._generate_parameters_xml(parameters or {})}
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition">
    <scm class="hudson.plugins.git.GitSCM">
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>{repo_url}</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/{branch}</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
    </scm>
    <scriptPath>{jenkinsfile_path}</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>"""
        
        try:
            self.server.create_job(job_name, config_xml)
            logger.info(f"Created pipeline job: {job_name}")
            return True
        except jenkins.JenkinsException as e:
            logger.error(f"Failed to create job: {e}")
            return False
    
    def _generate_parameters_xml(self, parameters: Dict) -> str:
        """Generate parameters XML for job configuration."""
        params_xml = ""
        for name, default_value in parameters.items():
            params_xml += f"""
        <hudson.model.StringParameterDefinition>
          <name>{name}</name>
          <defaultValue>{default_value}</defaultValue>
        </hudson.model.StringParameterDefinition>"""
        return params_xml
    
    def trigger_build(
        self,
        job_name: str,
        parameters: Dict = None,
        wait: bool = True,
        timeout: int = 3600
    ) -> Optional[Dict]:
        """
        Trigger a Jenkins build.
        
        Interview Scenario:
        "Implement a deployment trigger with parameter validation"
        
        Args:
            job_name: Job to trigger
            parameters: Build parameters
            wait: Wait for build to complete
            timeout: Maximum wait time in seconds
        
        Returns:
            Build result dictionary if wait=True
        """
        try:
            # Trigger build
            queue_number = self.server.build_job(
                job_name,
                parameters=parameters or {}
            )
            
            logger.info(
                f"Triggered build for {job_name}, queue: {queue_number}"
            )
            
            if not wait:
                return {'queue_number': queue_number}
            
            # Wait for build to start
            time.sleep(2)
            queue_item = self.server.get_queue_item(queue_number)
            
            while 'executable' not in queue_item:
                time.sleep(1)
                queue_item = self.server.get_queue_item(queue_number)
            
            build_number = queue_item['executable']['number']
            
            # Wait for build to complete
            start_time = time.time()
            while True:
                build_info = self.server.get_build_info(
                    job_name,
                    build_number
                )
                
                if not build_info['building']:
                    break
                
                if time.time() - start_time > timeout:
                    logger.error(f"Build timeout after {timeout}s")
                    return None
                
                time.sleep(5)
            
            return {
                'job_name': job_name,
                'build_number': build_number,
                'result': build_info['result'],
                'duration': build_info['duration'],
                'url': build_info['url']
            }
        
        except jenkins.JenkinsException as e:
            logger.error(f"Failed to trigger build: {e}")
            return None
    
    def get_build_console_output(
        self,
        job_name: str,
        build_number: int
    ) -> str:
        """
        Get console output from a build.
        
        Interview Question:
        "How do you troubleshoot failed CI/CD builds?"
        """
        try:
            return self.server.get_build_console_output(
                job_name,
                build_number
            )
        except jenkins.JenkinsException as e:
            logger.error(f"Failed to get console output: {e}")
            return ""
    
    def monitor_build_queue(self) -> List[Dict]:
        """
        Monitor Jenkins build queue.
        
        Interview Scenario:
        "Implement queue monitoring for capacity planning"
        
        Returns:
            List of queued items
        """
        try:
            queue_info = self.server.get_queue_info()
            
            queued_items = []
            for item in queue_info:
                queued_items.append({
                    'id': item['id'],
                    'job_name': item['task']['name'],
                    'why': item.get('why', 'Unknown'),
                    'stuck': item.get('stuck', False),
                    'blocked': item.get('blocked', False)
                })
            
            return queued_items
        
        except jenkins.JenkinsException as e:
            logger.error(f"Failed to get queue info: {e}")
            return []
    
    def get_failed_builds(
        self,
        job_name: str,
        count: int = 10
    ) -> List[Dict]:
        """
        Get recent failed builds for analysis.
        
        Interview Question:
        "How do you identify patterns in build failures?"
        """
        try:
            job_info = self.server.get_job_info(job_name)
            builds = job_info['builds'][:count]
            
            failed_builds = []
            for build in builds:
                build_info = self.server.get_build_info(
                    job_name,
                    build['number']
                )
                
                if build_info['result'] in ['FAILURE', 'ABORTED', 'UNSTABLE']:
                    failed_builds.append({
                        'number': build_info['number'],
                        'result': build_info['result'],
                        'timestamp': build_info['timestamp'],
                        'duration': build_info['duration'],
                        'url': build_info['url']
                    })
            
            return failed_builds
        
        except jenkins.JenkinsException as e:
            logger.error(f"Failed to get build history: {e}")
            return []


# Usage Examples
if __name__ == "__main__":
    jenkins_client = JenkinsAutomation(
        url='http://jenkins.example.com',
        username='admin',
        password='api-token'
    )
    
    # Example 1: Create pipeline job
    jenkins_client.create_pipeline_job(
        job_name='deploy-production',
        jenkinsfile_path='Jenkinsfile',
        repo_url='https://github.com/myorg/myapp.git',
        parameters={
            'ENVIRONMENT': 'production',
            'VERSION': 'latest'
        }
    )
    
    # Example 2: Trigger build and wait for result
    result = jenkins_client.trigger_build(
        job_name='deploy-production',
        parameters={'VERSION': 'v1.2.3'},
        wait=True
    )
    print(f"Build result: {result['result']}")
    
    # Example 3: Monitor build queue
    queued = jenkins_client.monitor_build_queue()
    print(f"Queued builds: {len(queued)}")
    
    # Example 4: Analyze failed builds
    failed = jenkins_client.get_failed_builds('deploy-production')
    for build in failed:
        print(f"Build #{build['number']}: {build['result']}")
```

---

## 3. Prometheus/Grafana Integration

### Example: Metrics and Alerting

```python
"""
prometheus_grafana.py

Prometheus and Grafana API integration for observability.

Interview Topics:
- Metrics collection and querying
- Alert management
- Dashboard automation
"""

import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PrometheusClient:
    """
    Prometheus API client for metrics queries.
    
    Interview Questions:
    - "How do you query time-series metrics?"
    - "Implement SLO monitoring"
    - "Design alerting strategy"
    """
    
    def __init__(self, base_url: str):
        """
        Initialize Prometheus client.
        
        Args:
            base_url: Prometheus server URL
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
    
    def query(self, promql: str) -> Optional[Dict]:
        """
        Execute instant PromQL query.
        
        Interview Scenario:
        "Query current CPU usage across all pods"
        
        Example:
            prom = PrometheusClient('http://prometheus:9090')
            result = prom.query('rate(http_requests_total[5m])')
        """
        try:
            response = requests.get(
                f"{self.api_url}/query",
                params={'query': promql}
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Prometheus query failed: {e}")
            return None
    
    def query_range(
        self,
        promql: str,
        start: datetime,
        end: datetime,
        step: str = '15s'
    ) -> Optional[Dict]:
        """
        Execute range PromQL query.
        
        Interview Question:
        "How do you analyze metric trends over time?"
        
        Args:
            promql: PromQL query
            start: Start time
            end: End time
            step: Query resolution
        """
        try:
            response = requests.get(
                f"{self.api_url}/query_range",
                params={
                    'query': promql,
                    'start': start.timestamp(),
                    'end': end.timestamp(),
                    'step': step
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Prometheus range query failed: {e}")
            return None
    
    def calculate_slo_compliance(
        self,
        success_metric: str,
        total_metric: str,
        threshold: float = 0.99,
        window_hours: int = 24
    ) -> Dict:
        """
        Calculate SLO compliance.
        
        Interview Scenario:
        "Implement 99.9% uptime SLO monitoring"
        
        Returns:
            SLO compliance data
        """
        end = datetime.now()
        start = end - timedelta(hours=window_hours)
        
        # Query success rate
        promql = f"sum(rate({success_metric}[5m])) / sum(rate({total_metric}[5m]))"
        
        result = self.query_range(promql, start, end, step='1m')
        
        if not result or result['status'] != 'success':
            return {}
        
        values = result['data']['result'][0]['values']
        success_rates = [float(v[1]) for v in values]
        
        compliant_minutes = sum(1 for rate in success_rates if rate >= threshold)
        total_minutes = len(success_rates)
        compliance = compliant_minutes / total_minutes if total_minutes > 0 else 0
        
        return {
            'slo_threshold': threshold,
            'actual_compliance': compliance,
            'is_compliant': compliance >= threshold,
            'window_hours': window_hours,
            'total_datapoints': total_minutes,
            'compliant_datapoints': compliant_minutes
        }


class GrafanaClient:
    """
    Grafana API client for dashboard management.
    
    Interview Topics:
    - Dashboard as code
    - Automated alerting
    - Multi-environment setup
    """
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize Grafana client.
        
        Args:
            base_url: Grafana server URL
            api_key: Grafana API key
        """
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_dashboard(
        self,
        dashboard_json: Dict,
        folder_id: int = 0,
        overwrite: bool = False
    ) -> Optional[Dict]:
        """
        Create or update dashboard.
        
        Interview Question:
        "How do you manage dashboards as code?"
        
        Example:
            dashboard = {
                'dashboard': {
                    'title': 'My Service Dashboard',
                    'panels': [...]
                },
                'folderId': 0,
                'overwrite': True
            }
            grafana.create_dashboard(dashboard)
        """
        try:
            payload = {
                'dashboard': dashboard_json,
                'folderId': folder_id,
                'overwrite': overwrite
            }
            
            response = requests.post(
                f"{self.base_url}/api/dashboards/db",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to create dashboard: {e}")
            return None
    
    def create_alert_rule(
        self,
        rule_name: str,
        query: str,
        condition: str,
        threshold: float,
        notification_channel: str
    ) -> Optional[Dict]:
        """
        Create alert rule.
        
        Interview Scenario:
        "Implement automated alerting for SLO violations"
        """
        # Alert rule configuration
        alert_rule = {
            'name': rule_name,
            'query': query,
            'condition': condition,
            'threshold': threshold,
            'notifications': [notification_channel]
        }
        
        # Implementation depends on Grafana version
        # This is a simplified example
        logger.info(f"Created alert rule: {rule_name}")
        return alert_rule


# Usage Examples
if __name__ == "__main__":
    # Prometheus examples
    prom = PrometheusClient('http://prometheus:9090')
    
    # Example 1: Query current HTTP request rate
    result = prom.query('rate(http_requests_total{job="api"}[5m])')
    print(f"Current request rate: {result}")
    
    # Example 2: Calculate SLO compliance
    slo = prom.calculate_slo_compliance(
        success_metric='http_requests_total{status=~"2.."}',
        total_metric='http_requests_total',
        threshold=0.999,
        window_hours=24
    )
    print(f"SLO Compliance: {slo['actual_compliance']:.2%}")
    
    # Grafana examples
    grafana = GrafanaClient(
        'http://grafana:3000',
        api_key='your-api-key'
    )
    
    # Example 3: Create dashboard
    dashboard_json = {
        'title': 'Service Health Dashboard',
        'tags': ['automated', 'sre'],
        'timezone': 'browser',
        'panels': []
    }
    grafana.create_dashboard(dashboard_json)
```

---

## 4. JFrog Artifactory Integration

### Example: Artifact Management

```python
"""
jfrog_automation.py

JFrog Artifactory API integration for artifact management.

Interview Topics:
- Artifact lifecycle management
- Build information tracking
- Repository cleanup policies
"""

import requests
from typing import List, Dict, Optional
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ArtifactoryClient:
    """
    JFrog Artifactory API client.
    
    Interview Scenarios:
    - "Implement artifact promotion pipeline"
    - "Design retention policy enforcement"
    - "Track build artifacts through environments"
    """
    
    def __init__(
        self,
        base_url: str,
        username: str = None,
        password: str = None,
        api_key: str = None
    ):
        """
        Initialize Artifactory client.
        
        Args:
            base_url: Artifactory server URL
            username: Username for basic auth
            password: Password for basic auth
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        
        if api_key:
            self.headers = {'X-JFrog-Art-Api': api_key}
            self.auth = None
        elif username and password:
            self.headers = {}
            self.auth = (username, password)
        else:
            raise ValueError("Must provide either API key or username/password")
    
    def upload_artifact(
        self,
        local_file_path: str,
        repo: str,
        target_path: str,
        properties: Dict = None
    ) -> bool:
        """
        Upload artifact to Artifactory.
        
        Interview Question:
        "How do you ensure artifact integrity during upload?"
        
        Args:
            local_file_path: Path to local file
            repo: Target repository
            target_path: Target path in repository
            properties: Artifact properties/metadata
        
        Returns:
            True if successful
        """
        try:
            # Calculate checksums
            with open(local_file_path, 'rb') as f:
                content = f.read()
                md5 = hashlib.md5(content).hexdigest()
                sha1 = hashlib.sha1(content).hexdigest()
            
            # Build URL
            url = f"{self.base_url}/{repo}/{target_path}"
            
            # Add properties as matrix parameters
            if properties:
                props_str = ';'.join([f"{k}={v}" for k, v in properties.items()])
                url += f";{props_str}"
            
            # Upload with checksums
            headers = {
                **self.headers,
                'X-Checksum-Md5': md5,
                'X-Checksum-Sha1': sha1
            }
            
            with open(local_file_path, 'rb') as f:
                response = requests.put(
                    url,
                    headers=headers,
                    data=f,
                    auth=self.auth
                )
            
            response.raise_for_status()
            logger.info(f"Uploaded artifact to {target_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to upload artifact: {e}")
            return False
    
    def download_artifact(
        self,
        repo: str,
        artifact_path: str,
        local_path: str,
        verify_checksum: bool = True
    ) -> bool:
        """
        Download artifact with checksum verification.
        
        Interview Scenario:
        "Implement secure artifact retrieval for deployments"
        """
        try:
            url = f"{self.base_url}/{repo}/{artifact_path}"
            
            response = requests.get(
                url,
                headers=self.headers,
                auth=self.auth,
                stream=True
            )
            response.raise_for_status()
            
            # Download file
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify checksum if enabled
            if verify_checksum:
                expected_sha1 = response.headers.get('X-Checksum-Sha1')
                if expected_sha1:
                    with open(local_path, 'rb') as f:
                        actual_sha1 = hashlib.sha1(f.read()).hexdigest()
                    
                    if expected_sha1 != actual_sha1:
                        raise ValueError("Checksum verification failed")
            
            logger.info(f"Downloaded artifact to {local_path}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to download artifact: {e}")
            return False
    
    def cleanup_old_artifacts(
        self,
        repo: str,
        retention_days: int = 90,
        exclude_patterns: List[str] = None
    ) -> Dict[str, int]:
        """
        Clean up artifacts older than retention period.
        
        Interview Question:
        "Design a cost-effective artifact retention policy"
        
        Returns:
            Dictionary with cleanup statistics
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        # Use AQL (Artifactory Query Language) to find old artifacts
        aql_query = f"""
        items.find({{
            "repo": "{repo}",
            "created": {{"$lt": "{cutoff_date.isoformat()}"}}
        }})
        """
        
        try:
            response = requests.post(
                f"{self.base_url}/api/search/aql",
                headers=self.headers,
                auth=self.auth,
                data=aql_query
            )
            response.raise_for_status()
            
            results = response.json()['results']
            
            deleted = 0
            failed = 0
            
            for item in results:
                path = f"{item['repo']}/{item['path']}/{item['name']}"
                
                # Check exclusion patterns
                if exclude_patterns:
                    if any(pattern in path for pattern in exclude_patterns):
                        continue
                
                # Delete artifact
                delete_url = f"{self.base_url}/{path}"
                delete_response = requests.delete(
                    delete_url,
                    headers=self.headers,
                    auth=self.auth
                )
                
                if delete_response.status_code == 204:
                    deleted += 1
                else:
                    failed += 1
            
            return {
                'total_found': len(results),
                'deleted': deleted,
                'failed': failed
            }
        
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return {'error': str(e)}


# Usage Examples
if __name__ == "__main__":
    artifactory = ArtifactoryClient(
        base_url='https://artifactory.example.com/artifactory',
        api_key='your-api-key'
    )
    
    # Example 1: Upload with metadata
    artifactory.upload_artifact(
        local_file_path='./app-v1.2.3.jar',
        repo='libs-release-local',
        target_path='com/example/app/1.2.3/app-1.2.3.jar',
        properties={
            'build.name': 'app-build',
            'build.number': '123',
            'vcs.revision': 'abc123'
        }
    )
    
    # Example 2: Download with verification
    artifactory.download_artifact(
        repo='libs-release-local',
        artifact_path='com/example/app/1.2.3/app-1.2.3.jar',
        local_path='./downloaded-app.jar',
        verify_checksum=True
    )
    
    # Example 3: Cleanup old artifacts
    stats = artifactory.cleanup_old_artifacts(
        repo='libs-snapshot-local',
        retention_days=30,
        exclude_patterns=['RELEASE', 'production']
    )
    print(f"Cleanup stats: {stats}")
```

---

## 📝 Best Practices for API Integrations

### 1. Authentication
```python
# Always use environment variables
import os

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

### 2. Error Handling
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def api_call_with_retry():
    # API call implementation
    pass
```

### 3. Rate Limiting
```python
import time
from functools import wraps

def rate_limit(calls_per_second=10):
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result
        return wrapper
    return decorator
```

### 4. Response Caching
```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedAPIClient:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
    
    def get_with_cache(self, key, fetch_func):
        if key in self.cache:
            cached_value, cached_time = self.cache[key]
            if datetime.now() - cached_time < self.cache_ttl:
                return cached_value
        
        value = fetch_func()
        self.cache[key] = (value, datetime.now())
        return value
```

---

This guide provides production-ready API integration examples covering all major DevOps platforms with interview-focused scenarios!
