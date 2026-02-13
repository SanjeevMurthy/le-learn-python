# Code Examples Guide - Detailed Implementation

## 📋 Example Structure Standards

Each code file should follow this pattern:
1. Module docstring
2. Imports (standard lib, third-party, local)
3. Constants and Configuration
4. Simple Functions (NOT classes)
5. Main execution block with examples
6. Extensive inline comments explaining every step

**Key Principles:**
- ✅ Use simple functions, NOT classes
- ✅ Add inline comments for EVERY logical step
- ✅ Explain WHY, not just WHAT
- ✅ Include both AWS and GCP examples
- ✅ Keep functions small and focused (single responsibility)

---

## 1. Core Python Patterns

### Example: Retry Logic with Exponential Backoff

```python
"""
retry_decorator.py

Implements retry logic with exponential backoff for resilient API calls.
This is a fundamental pattern used across all DevOps/SRE automation.

Interview Topics:
- Why exponential backoff vs fixed delay
- Decorators in Python
- Exception handling strategies
- Preventing thundering herd problem

Production Use Cases:
- API calls to external services
- Database connection retries
- Cloud API operations (AWS, GCP, Azure)
"""

import time
import functools
import logging
from typing import Callable, Tuple, Type

# Configure logging to see retry attempts
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator that retries a function with exponential backoff.
    
    How it works:
    1. Try the function
    2. If it fails, wait initial_delay seconds
    3. Try again, if fails, wait initial_delay * backoff_factor
    4. Continue until max_retries reached or success
    
    Args:
        max_retries: How many times to retry (default 3)
        initial_delay: First wait time in seconds (default 1.0)
        backoff_factor: Multiply delay by this each retry (default 2.0)
        exceptions: Which exceptions to catch and retry (default all)
    
    Example delays with defaults:
        Attempt 1: Fail, wait 1 second
        Attempt 2: Fail, wait 2 seconds (1 * 2)
        Attempt 3: Fail, wait 4 seconds (2 * 2)
        Attempt 4: Final try
    
    Interview Question:
        Q: Why exponential backoff instead of fixed delay?
        A: 
        1. Prevents "thundering herd" - many clients retrying at same time
        2. Gives failing service time to recover
        3. More respectful of rate limits
        4. Reduces network congestion
    """
    # This is the outer decorator function that receives the parameters
    def decorator(func: Callable) -> Callable:
        # This preserves the original function's name and docstring
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Start with the initial delay value
            delay = initial_delay
            # Keep track of the last exception for final raise
            last_exception = None
            
            # Loop through retry attempts (max_retries + 1 for initial try)
            for attempt in range(max_retries + 1):
                try:
                    # Try to execute the original function
                    result = func(*args, **kwargs)
                    # If successful, return immediately
                    return result
                    
                except exceptions as e:
                    # Store this exception in case all retries fail
                    last_exception = e
                    
                    # Check if this was the last retry attempt
                    if attempt == max_retries:
                        # Log final failure with full stack trace
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries",
                            exc_info=True
                        )
                        # Re-raise the exception to caller
                        raise
                    
                    # Log the retry attempt (not the final one)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: "
                        f"{str(e)}. Waiting {delay} seconds before retry..."
                    )
                    
                    # Wait before next retry
                    time.sleep(delay)
                    
                    # Increase delay for next attempt (exponential backoff)
                    delay *= backoff_factor
            
            # If we somehow get here, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


# Example: Simple function to check if a service is healthy
@retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
def check_service_health(url: str) -> dict:
    """
    Check if a service endpoint is healthy.
    
    This function will automatically retry with exponential backoff
    if it fails (because of the @retry_with_backoff decorator).
    
    Args:
        url: The health check endpoint URL
        
    Returns:
        Dictionary with health status
        
    Raises:
        requests.RequestException: If health check fails after all retries
    """
    import requests
    
    # Make HTTP GET request to health endpoint
    # timeout=5 means wait max 5 seconds for response
    response = requests.get(url, timeout=5)
    
    # Raise exception if status code is 4xx or 5xx
    # This will trigger the retry logic
    response.raise_for_status()
    
    # Return the JSON response as a dictionary
    return response.json()


# Usage Examples
if __name__ == "__main__":
    import requests
    
    print("Example 1: Checking service health with auto-retry")
    print("-" * 50)
    
    try:
        # This will automatically retry up to 3 times if it fails
        health = check_service_health("https://api.example.com/health")
        print(f"Service is healthy: {health}")
    except requests.RequestException as e:
        print(f"Service is down after all retries: {e}")
    
    print("\nExample 2: Custom function with retry")
    print("-" * 50)
    
    # Define a function that might fail sometimes
    @retry_with_backoff(max_retries=5, initial_delay=0.5)
    def fetch_user_data(user_id: int) -> dict:
        """Fetch user data from API with automatic retries."""
        import requests
        
        # Build the API URL
        url = f"https://api.example.com/users/{user_id}"
        
        # Make the request
        response = requests.get(url, timeout=10)
        
        # Check if request was successful (200 OK)
        response.raise_for_status()
        
        # Parse and return JSON data
        return response.json()
    
    try:
        user = fetch_user_data(123)
        print(f"User data: {user}")
    except Exception as e:
        print(f"Failed to fetch user: {e}")
```

---

## 2. Cloud Automation Examples

### AWS Example: EC2 Instance Management

```python
"""
ec2_management.py

Simple EC2 instance management functions for common DevOps tasks.
Uses functional programming approach - no classes, just simple functions.

Interview Scenario: "Automate instance lifecycle management"

Production Use Cases:
- Cost optimization by stopping dev/test instances after hours
- Automated backup creation via AMI snapshots
- Auto-remediation for unhealthy instances
- Tag-based resource management

Prerequisites:
- boto3 installed: pip install boto3
- AWS credentials configured (use aws configure or environment variables)
- IAM permissions for EC2 operations
"""

import boto3
from typing import List, Dict
from datetime import datetime, timedelta
import logging

# Set up logging so we can see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_ec2_client(region: str = 'us-east-1'):
    """
    Create and return an EC2 client for the specified region.
    
    This is a simple helper function to create boto3 clients.
    By centralizing client creation, we can:
    1. Easily change regions
    2. Add retry configuration in one place
    3. Handle credential errors consistently
    
    Args:
        region: AWS region name (default: us-east-1)
        
    Returns:
        boto3 EC2 client object
        
    Interview Tip:
        Always create clients at the function level, not globally.
        This makes testing easier (you can mock the client).
    """
    # Create boto3 client for EC2 service
    # boto3 automatically looks for credentials in:
    # 1. Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
    # 2. ~/.aws/credentials file
    # 3. IAM role (if running on EC2)
    client = boto3.client('ec2', region_name=region)
    
    logger.info(f"Created EC2 client for region: {region}")
    return client


def list_instances_by_tag(tag_key: str, tag_value: str, region: str = 'us-east-1') -> List[Dict]:
    """
    Find all EC2 instances with a specific tag.
    
    Real-world use case:
    - Find all instances tagged Environment=dev to stop them after hours
    - List all instances for a specific project
    - Identify instances by team or cost center
    
    Args:
        tag_key: The tag name to search for (e.g., 'Environment', 'Team', 'Project')
        tag_value: The tag value to match (e.g., 'dev', 'production', 'my-team')
        region: AWS region to search in
        
    Returns:
        List of dictionaries, each containing instance information:
        - instance_id: The EC2 instance ID (i-xxxxx)
        - instance_type: Size of instance (t2.micro, m5.large, etc.)
        - state: Current state (running, stopped, terminated)
        - launch_time: When the instance was started
        - tags: All tags on the instance
        
    Example:
        # Find all development instances
        dev_instances = list_instances_by_tag('Environment', 'dev')
        for instance in dev_instances:
            print(f"Found: {instance['instance_id']} - {instance['state']}")
    
    Interview Question:
        Q: How do you handle pagination in AWS API calls?
        A: AWS APIs return max 1000 results. For more, use NextToken.
           Boto3 handles this automatically with describe_instances().
    """
    # Get EC2 client for the specified region
    ec2_client = get_ec2_client(region)
    
    # Create filters for the API call
    # Filters reduce the amount of data returned and make queries faster
    filters = [
        # Filter by tag - format is 'tag:TagName'
        {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
        # Only get running or stopped instances (exclude terminated)
        {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
    ]
    
    logger.info(f"Searching for instances with tag {tag_key}={tag_value}")
    
    # Call AWS API to get instances matching our filters
    # This returns a complex nested dictionary
    response = ec2_client.describe_instances(Filters=filters)
    
    # Initialize empty list to store our simplified instance data
    instances = []
    
    # AWS returns instances grouped by 'Reservations'
    # Each reservation can have multiple instances
    for reservation in response['Reservations']:
        # Loop through each instance in this reservation
        for instance in reservation['Instances']:
            # Extract only the information we care about
            instance_info = {
                'instance_id': instance['InstanceId'],
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'launch_time': instance['LaunchTime'],
                # Convert tags list to dictionary for easier access
                # Tags come as [{'Key': 'Name', 'Value': 'MyServer'}, ...]
                # We convert to {'Name': 'MyServer', ...}
                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
            }
            
            instances.append(instance_info)
    
    logger.info(f"Found {len(instances)} instances")
    return instances


def stop_instances_by_tag(tag_key: str = 'AutoStop', tag_value: str = 'true', 
                          region: str = 'us-east-1') -> Dict[str, List[str]]:
    """
    Stop all EC2 instances that have a specific tag.
    
    Cost Optimization Use Case:
    Tag your dev/test instances with AutoStop=true, then run this function
    via a scheduled Lambda at 6 PM to stop them automatically.
    This can save 70% on dev/test costs if instances run only during work hours.
    
    Args:
        tag_key: Tag name to look for (default: AutoStop)
        tag_value: Tag value to match (default: true)
        region: AWS region
        
    Returns:
        Dictionary with two lists:
        - 'stopped': Instance IDs that were successfully stopped
        - 'failed': Instance IDs that failed to stop
        
    Example:
        # Stop all instances tagged AutoStop=true
        result = stop_instances_by_tag()
        print(f"Stopped {len(result['stopped'])} instances")
        print(f"Failed to stop {len(result['failed'])} instances")
    
    Interview Scenario:
        Q: Design a cost optimization script to stop dev instances after hours
        A: This is the solution! Use tags to mark stoppable instances,
           run this function on a schedule (Lambda + EventBridge),
           send Slack notification with results.
    """
    # First, find all instances with the specified tag
    instances = list_instances_by_tag(tag_key, tag_value, region)
    
    # Filter to only get instances that are currently running
    # No point trying to stop an instance that's already stopped
    running_instances = [
        inst['instance_id'] 
        for inst in instances 
        if inst['state'] == 'running'
    ]
    
    # Initialize result dictionary
    result = {'stopped': [], 'failed': []}
    
    # If no running instances found, return early
    if not running_instances:
        logger.info("No running instances found to stop")
        return result
    
    # Get EC2 client
    ec2_client = get_ec2_client(region)
    
    logger.info(f"Attempting to stop {len(running_instances)} instances")
    
    try:
        # Call AWS API to stop the instances
        # This is an async operation - instances don't stop immediately
        response = ec2_client.stop_instances(InstanceIds=running_instances)
        
        # Check the response to see which instances are stopping
        for instance in response['StoppingInstances']:
            instance_id = instance['InstanceId']
            current_state = instance['CurrentState']['Name']
            
            # If state is 'stopping', it's working
            if current_state == 'stopping':
                result['stopped'].append(instance_id)
                logger.info(f"✓ Stopped instance: {instance_id}")
            else:
                # Something went wrong
                result['failed'].append(instance_id)
                logger.warning(f"✗ Failed to stop instance: {instance_id}")
    
    except Exception as e:
        # If the API call fails completely, all instances failed
        logger.error(f"Failed to stop instances: {e}")
        result['failed'].extend(running_instances)
    
    return result


def create_ami_backup(instance_id: str, retention_days: int = 7, 
                      region: str = 'us-east-1') -> Dict:
    """
    Create an AMI (Amazon Machine Image) backup of an EC2 instance.
    
    Disaster Recovery Use Case:
    - Create nightly backups of production instances
    - Snapshot before major deployments
    - Enable quick recovery from failures
    
    How AMI backups work:
    1. AWS creates snapshots of all attached EBS volumes
    2. AMI references these snapshots
    3. You can launch new instances from the AMI
    4. Original instance keeps running (NoReboot=True)
    
    Args:
        instance_id: The EC2 instance ID to backup (e.g., i-1234567890abcdef0)
        retention_days: How many days to keep the backup (default: 7)
        region: AWS region
        
    Returns:
        Dictionary with backup information:
        - ami_id: The created AMI ID
        - ami_name: Name given to the AMI
        - instance_id: Source instance ID
        - deletion_date: When this backup will be deleted
        
    Example:
        # Create a backup of instance, keep for 30 days
        backup = create_ami_backup('i-1234567890abcdef0', retention_days=30)
        print(f"Backup created: {backup['ami_id']}")
        print(f"Will be deleted on: {backup['deletion_date']}")
    
    Interview Question:
        Q: How would you implement automated DR for EC2?
        A: 
        1. Schedule this function daily (Lambda + EventBridge)
        2. Tag instances that need backups
        3. Copy AMIs to different region for geo-redundancy
        4. Implement cleanup function to delete old AMIs
        5. Monitor backup success/failure
    """
    # Get EC2 client
    ec2_client = get_ec2_client(region)
    
    # Create a descriptive name for the AMI
    # Include instance ID and timestamp for easy identification
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    ami_name = f"backup-{instance_id}-{timestamp}"
    
    logger.info(f"Creating AMI backup for instance {instance_id}")
    
    try:
        # Call AWS API to create the AMI
        # NoReboot=True means instance stays running during backup
        # This prevents downtime but might result in inconsistent backups
        # For databases, use NoReboot=False or stop the instance first
        response = ec2_client.create_image(
            InstanceId=instance_id,
            Name=ami_name,
            Description=f"Automated backup created on {datetime.now()}",
            NoReboot=True  # Keep instance running
        )
        
        # Get the AMI ID from response
        ami_id = response['ImageId']
        
        # Calculate when this backup should be deleted
        deletion_date = datetime.now() + timedelta(days=retention_days)
        deletion_date_str = deletion_date.strftime('%Y-%m-%d')
        
        # Tag the AMI for lifecycle management
        # These tags help automated cleanup scripts identify old backups
        ec2_client.create_tags(
            Resources=[ami_id],
            Tags=[
                # When to delete this backup
                {'Key': 'DeleteAfter', 'Value': deletion_date_str},
                # Which instance this came from
                {'Key': 'SourceInstance', 'Value': instance_id},
                # Mark this as an automated backup
                {'Key': 'BackupType', 'Value': 'Automated'},
                # Add creation timestamp
                {'Key': 'CreatedAt', 'Value': datetime.now().isoformat()}
            ]
        )
        
        logger.info(f"✓ Created AMI {ami_id}, will be deleted on {deletion_date_str}")
        
        # Return backup information
        return {
            'ami_id': ami_id,
            'ami_name': ami_name,
            'instance_id': instance_id,
            'deletion_date': deletion_date_str,
            'created_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"✗ Failed to create AMI: {e}")
        raise


# Usage Examples
if __name__ == "__main__":
    print("AWS EC2 Automation Examples")
    print("=" * 60)
    
    # Example 1: List all development instances
    print("\nExample 1: Finding development instances")
    print("-" * 60)
    dev_instances = list_instances_by_tag('Environment', 'dev', region='us-east-1')
    print(f"Found {len(dev_instances)} dev instances:")
    for inst in dev_instances:
        print(f"  - {inst['instance_id']}: {inst['state']} ({inst['instance_type']})")
    
    # Example 2: Stop instances tagged for auto-stop
    print("\nExample 2: Stopping instances tagged AutoStop=true")
    print("-" * 60)
    result = stop_instances_by_tag('AutoStop', 'true')
    print(f"Successfully stopped: {result['stopped']}")
    print(f"Failed to stop: {result['failed']}")
    
    # Example 3: Create backup of a specific instance
    print("\nExample 3: Creating AMI backup")
    print("-" * 60)
    # Replace with your actual instance ID
    # backup = create_ami_backup('i-1234567890abcdef0', retention_days=7)
    # print(f"Backup created: {backup['ami_id']}")
    # print(f"Will be deleted on: {backup['deletion_date']}")
    print("(Commented out - replace with your instance ID to test)")
```

---

### GCP Example: Compute Engine Instance Management

```python
"""
gce_management.py

Simple Google Compute Engine instance management functions.
Equivalent to AWS EC2 but for Google Cloud Platform.

Interview Scenario: "Automate GCP instance lifecycle management"

Production Use Cases:
- Cost optimization by stopping dev instances after hours
- Automated snapshot backups
- Auto-remediation for unhealthy instances
- Label-based resource management (GCP uses labels like AWS tags)

Prerequisites:
- google-cloud-compute installed: pip install google-cloud-compute
- GCP credentials configured (use gcloud auth application-default login)
- IAM permissions for Compute Engine operations
"""

from google.cloud import compute_v1
from typing import List, Dict
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_instances_client():
    """
    Create and return a GCP Compute Engine instances client.
    
    GCP uses Application Default Credentials (ADC) which looks for credentials in:
    1. GOOGLE_APPLICATION_CREDENTIALS environment variable (JSON key file)
    2. gcloud auth application-default login
    3. Service account when running on GCE/GKE
    
    Returns:
        compute_v1.InstancesClient object
        
    Interview Tip:
        GCP's client libraries are different from AWS boto3.
        They use separate clients for different resources
        (InstancesClient, DisksClient, etc.)
    """
    # Create client for Compute Engine instances
    # This automatically uses Application Default Credentials
    client = compute_v1.InstancesClient()
    
    logger.info("Created GCP Compute Engine client")
    return client


def list_instances_by_label(
    project_id: str,
    zone: str,
    label_key: str,
    label_value: str
) -> List[Dict]:
    """
    Find all GCE instances with a specific label.
    
    GCP uses labels (similar to AWS tags) to organize resources.
    Labels are key-value pairs attached to resources.
    
    Args:
        project_id: Your GCP project ID (e.g., 'my-project-123')
        zone: GCP zone (e.g., 'us-central1-a')
        label_key: The label key to search for (e.g., 'environment', 'team')
        label_value: The label value to match (e.g., 'dev', 'production')
        
    Returns:
        List of dictionaries with instance information:
        - instance_id: Numeric instance ID
        - name: Instance name
        - machine_type: Instance size (e2-micro, n1-standard-1, etc.)
        - status: Current status (RUNNING, TERMINATED, etc.)
        - zone: Where the instance is located
        - labels: All labels on the instance
        
    Example:
        # Find all dev instances in us-central1-a
        instances = list_instances_by_label(
            project_id='my-project',
            zone='us-central1-a',
            label_key='environment',
            label_value='dev'
        )
        for inst in instances:
            print(f"Found: {inst['name']} - {inst['status']}")
    
    Interview Question:
        Q: What's the difference between AWS regions/AZs and GCP regions/zones?
        A: Similar concept but different naming:
           - AWS: us-east-1 (region), us-east-1a (AZ)
           - GCP: us-central1 (region), us-central1-a (zone)
    """
    # Get the instances client
    client = get_instances_client()
    
    logger.info(f"Searching for instances with label {label_key}={label_value}")
    
    # Call GCP API to list all instances in the zone
    # Unlike AWS, GCP requires you to specify project and zone explicitly
    request = compute_v1.ListInstancesRequest(
        project=project_id,
        zone=zone
    )
    
    # This returns an iterator of Instance objects
    instances_iterator = client.list(request=request)
    
    # Initialize list to store matching instances
    matching_instances = []
    
    # Loop through all instances in the zone
    for instance in instances_iterator:
        # Check if this instance has the label we're looking for
        # instance.labels is a dictionary like {'environment': 'dev', 'team': 'platform'}
        if instance.labels.get(label_key) == label_value:
            # Extract machine type name from full URL
            # Full URL: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/machineTypes/e2-medium
            # We just want: e2-medium
            machine_type_parts = instance.machine_type.split('/')
            machine_type = machine_type_parts[-1] if machine_type_parts else instance.machine_type
            
            # Create simplified instance info
            instance_info = {
                'instance_id': instance.id,
                'name': instance.name,
                'machine_type': machine_type,
                'status': instance.status,
                'zone': zone,
                'labels': dict(instance.labels) if instance.labels else {}
            }
            
            matching_instances.append(instance_info)
    
    logger.info(f"Found {len(matching_instances)} instances")
    return matching_instances


def stop_instances_by_label(
    project_id: str,
    zone: str,
    label_key: str = 'auto-stop',
    label_value: str = 'true'
) -> Dict[str, List[str]]:
    """
    Stop all GCE instances that have a specific label.
    
    Cost Optimization:
    Label your dev/test instances with auto-stop=true, then run this function
    on a schedule (Cloud Scheduler + Cloud Functions) at 6 PM to stop them.
    
    Args:
        project_id: GCP project ID
        zone: GCP zone where instances are located
        label_key: Label key to search for (default: auto-stop)
        label_value: Label value to match (default: true)
        
    Returns:
        Dictionary with two lists:
        - 'stopped': Instance names that were successfully stopped
        - 'failed': Instance names that failed to stop
        
    Example:
        # Stop all instances labeled auto-stop=true
        result = stop_instances_by_label(
            project_id='my-project',
            zone='us-central1-a'
        )
        print(f"Stopped: {result['stopped']}")
        print(f"Failed: {result['failed']}")
    
    Interview Scenario:
        Q: How would you automate cost savings in GCP?
        A: 
        1. Label instances with auto-stop=true
        2. Create Cloud Function with this code
        3. Use Cloud Scheduler to trigger function at 6 PM
        4. Send results to Slack/email
        5. Monitor savings in Billing dashboard
    """
    # Find all instances with the specified label
    instances = list_instances_by_label(project_id, zone, label_key, label_value)
    
    # Filter to only running instances
    # GCP status is 'RUNNING', 'TERMINATED', etc. (uppercase)
    running_instances = [
        inst for inst in instances 
        if inst['status'] == 'RUNNING'
    ]
    
    # Initialize result dictionary
    result = {'stopped': [], 'failed': []}
    
    # Return early if nothing to stop
    if not running_instances:
        logger.info("No running instances found to stop")
        return result
    
    # Get the instances client
    client = get_instances_client()
    
    logger.info(f"Attempting to stop {len(running_instances)} instances")
    
    # Loop through each instance and stop it
    # Unlike AWS which can stop multiple instances in one call,
    # GCP requires separate API call for each instance
    for instance in running_instances:
        instance_name = instance['name']
        
        try:
            # Create request to stop the instance
            request = compute_v1.StopInstanceRequest(
                project=project_id,
                zone=zone,
                instance=instance_name
            )
            
            # Call API to stop instance
            # This returns an Operation object (async operation)
            operation = client.stop(request=request)
            
            # We're not waiting for operation to complete here
            # In production, you might want to use operation.result() to wait
            
            result['stopped'].append(instance_name)
            logger.info(f"✓ Stopping instance: {instance_name}")
            
        except Exception as e:
            # If stop fails, add to failed list
            result['failed'].append(instance_name)
            logger.error(f"✗ Failed to stop {instance_name}: {e}")
    
    return result


def create_instance_snapshot(
    project_id: str,
    zone: str,
    instance_name: str,
    snapshot_prefix: str = 'backup'
) -> Dict:
    """
    Create disk snapshots for all disks attached to a GCE instance.
    
    GCP Backup Strategy:
    Unlike AWS AMI (which is one object), GCP creates individual snapshots
    for each disk. To backup an instance:
    1. Create snapshot of boot disk
    2. Create snapshots of any additional disks
    3. Tag snapshots with metadata
    
    Args:
        project_id: GCP project ID
        zone: Zone where instance is located
        instance_name: Name of the instance to backup
        snapshot_prefix: Prefix for snapshot names (default: backup)
        
    Returns:
        Dictionary with snapshot information:
        - instance_name: Source instance
        - snapshots: List of created snapshot names
        - created_at: Timestamp
        
    Example:
        # Create backup snapshots for an instance
        result = create_instance_snapshot(
            project_id='my-project',
            zone='us-central1-a',
            instance_name='web-server-1'
        )
        print(f"Created snapshots: {result['snapshots']}")
    
    Interview Question:
        Q: What's the difference between GCP snapshots and machine images?
        A:
        - Snapshots: Individual disk backups, incremental, cheaper
        - Machine Images: Full instance config + all disks, easier to restore
        - Use snapshots for regular backups, machine images for DR/migration
    """
    # Get clients for instances and disks
    instances_client = get_instances_client()
    disks_client = compute_v1.DisksClient()
    
    logger.info(f"Creating snapshots for instance {instance_name}")
    
    # Get instance details to find attached disks
    request = compute_v1.GetInstanceRequest(
        project=project_id,
        zone=zone,
        instance=instance_name
    )
    instance = instances_client.get(request=request)
    
    # Initialize list to track created snapshots
    created_snapshots = []
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    # Loop through all disks attached to the instance
    for disk in instance.disks:
        # Extract disk name from source URL
        # URL: https://www.googleapis.com/compute/v1/projects/my-project/zones/us-central1-a/disks/my-disk
        # We want: my-disk
        disk_name = disk.source.split('/')[-1]
        
        # Create snapshot name
        snapshot_name = f"{snapshot_prefix}-{disk_name}-{timestamp}"
        
        try:
            # Create snapshot request
            snapshot_body = compute_v1.Snapshot(
                name=snapshot_name,
                # Add labels for lifecycle management
                labels={
                    'source-instance': instance_name,
                    'backup-type': 'automated',
                    'created-by': 'python-script'
                },
                description=f"Automated snapshot of {disk_name} from {instance_name}"
            )
            
            # Create the snapshot
            request = compute_v1.InsertSnapshotRequest(
                project=project_id,
                snapshot_resource=snapshot_body,
                disk=disk_name,
                zone=zone
            )
            
            operation = disks_client.create_snapshot(request=request)
            
            created_snapshots.append(snapshot_name)
            logger.info(f"✓ Creating snapshot: {snapshot_name}")
            
        except Exception as e:
            logger.error(f"✗ Failed to snapshot {disk_name}: {e}")
    
    return {
        'instance_name': instance_name,
        'snapshots': created_snapshots,
        'created_at': datetime.now().isoformat()
    }


# Usage Examples
if __name__ == "__main__":
    print("GCP Compute Engine Automation Examples")
    print("=" * 60)
    
    # !!! IMPORTANT: Replace these with your actual values !!!
    PROJECT_ID = 'your-project-id'  # Your GCP project ID
    ZONE = 'us-central1-a'  # Your GCP zone
    
    # Example 1: List instances by label
    print("\nExample 1: Finding development instances")
    print("-" * 60)
    # dev_instances = list_instances_by_label(
    #     project_id=PROJECT_ID,
    #     zone=ZONE,
    #     label_key='environment',
    #     label_value='dev'
    # )
    # print(f"Found {len(dev_instances)} dev instances")
    # for inst in dev_instances:
    #     print(f"  - {inst['name']}: {inst['status']} ({inst['machine_type']})")
    print("(Commented out - set PROJECT_ID and ZONE to test)")
    
    # Example 2: Stop instances by label
    print("\nExample 2: Stopping instances labeled auto-stop=true")
    print("-" * 60)
    # result = stop_instances_by_label(
    #     project_id=PROJECT_ID,
    #     zone=ZONE,
    #     label_key='auto-stop',
    #     label_value='true'
    # )
    # print(f"Stopped: {result['stopped']}")
    # print(f"Failed: {result['failed']}")
    print("(Commented out - set PROJECT_ID and ZONE to test)")
    
    # Example 3: Create snapshots
    print("\nExample 3: Creating instance snapshots")
    print("-" * 60)
    # result = create_instance_snapshot(
    #     project_id=PROJECT_ID,
    #     zone=ZONE,
    #     instance_name='your-instance-name'
    # )
    # print(f"Created snapshots: {result['snapshots']}")
    print("(Commented out - set PROJECT_ID, ZONE and instance name to test)")
```
    """
    Manages EC2 instances with common DevOps operations.
    
    Interview Questions:
        Q: How do you handle AWS API rate limits?
        A: Implement exponential backoff, use pagination, batch operations
        
        Q: How do you ensure idempotent operations?
        A: Check current state before modification, use tags for tracking
    """
    
    def __init__(self, region: str = 'us-east-1'):
        """Initialize EC2 client."""
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.region = region
    
    def list_instances_by_tag(
        self,
        tag_key: str,
        tag_value: str
    ) -> List[Dict]:
        """
        List instances matching specific tag.
        
        Args:
            tag_key: Tag key to filter on
            tag_value: Tag value to match
        
        Returns:
            List of instance details
        
        Example:
            manager = EC2Manager()
            instances = manager.list_instances_by_tag('Environment', 'dev')
        """
        filters = [
            {'Name': f'tag:{tag_key}', 'Values': [tag_value]},
            {'Name': 'instance-state-name', 'Values': ['running', 'stopped']}
        ]
        
        response = self.ec2_client.describe_instances(Filters=filters)
        
        instances = []
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append({
                    'instance_id': instance['InstanceId'],
                    'instance_type': instance['InstanceType'],
                    'state': instance['State']['Name'],
                    'launch_time': instance['LaunchTime'],
                    'tags': {tag['Key']: tag['Value'] 
                            for tag in instance.get('Tags', [])}
                })
        
        return instances
    
    def stop_instances_by_schedule(
        self,
        tag_key: str = 'AutoStop',
        tag_value: str = 'true'
    ) -> Dict[str, List[str]]:
        """
        Stop instances marked for automatic shutdown.
        
        Common Interview Scenario:
        "Design a cost optimization script to stop dev instances after hours"
        
        Returns:
            Dictionary with 'stopped' and 'failed' instance IDs
        """
        instances = self.list_instances_by_tag(tag_key, tag_value)
        
        running_instances = [
            inst['instance_id'] 
            for inst in instances 
            if inst['state'] == 'running'
        ]
        
        result = {'stopped': [], 'failed': []}
        
        if not running_instances:
            logger.info("No running instances found to stop")
            return result
        
        try:
            response = self.ec2_client.stop_instances(
                InstanceIds=running_instances
            )
            
            for instance in response['StoppingInstances']:
                instance_id = instance['InstanceId']
                if instance['CurrentState']['Name'] == 'stopping':
                    result['stopped'].append(instance_id)
                    logger.info(f"Stopped instance: {instance_id}")
                else:
                    result['failed'].append(instance_id)
        
        except Exception as e:
            logger.error(f"Failed to stop instances: {e}")
            result['failed'].extend(running_instances)
        
        return result
    
    def create_ami_backup(
        self,
        instance_id: str,
        backup_name: Optional[str] = None,
        retention_days: int = 7
    ) -> Dict[str, str]:
        """
        Create AMI backup of an instance.
        
        Interview Question:
            Q: How would you implement automated DR for EC2?
            A: Scheduled AMI creation, cross-region copy, lifecycle policies
        
        Returns:
            Dictionary with AMI details
        """
        if not backup_name:
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup_name = f"backup-{instance_id}-{timestamp}"
        
        try:
            response = self.ec2_client.create_image(
                InstanceId=instance_id,
                Name=backup_name,
                Description=f"Automated backup created on {datetime.now()}",
                NoReboot=True  # Avoid downtime
            )
            
            ami_id = response['ImageId']
            
            # Tag the AMI for lifecycle management
            deletion_date = (
                datetime.now() + timedelta(days=retention_days)
            ).strftime('%Y-%m-%d')
            
            self.ec2_client.create_tags(
                Resources=[ami_id],
                Tags=[
                    {'Key': 'DeleteAfter', 'Value': deletion_date},
                    {'Key': 'SourceInstance', 'Value': instance_id},
                    {'Key': 'BackupType', 'Value': 'Automated'}
                ]
            )
            
            logger.info(f"Created AMI {ami_id} for instance {instance_id}")
            
            return {
                'ami_id': ami_id,
                'ami_name': backup_name,
                'instance_id': instance_id,
                'deletion_date': deletion_date
            }
        
        except Exception as e:
            logger.error(f"Failed to create AMI: {e}")
            raise
    
    def cleanup_old_snapshots(self, retention_days: int = 30) -> int:
        """
        Delete snapshots older than retention period.
        
        Interview Scenario:
        "Implement cost optimization by cleaning up old backups"
        
        Returns:
            Number of snapshots deleted
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        snapshots = self.ec2_client.describe_snapshots(
            OwnerIds=['self']
        )['Snapshots']
        
        deleted_count = 0
        
        for snapshot in snapshots:
            snapshot_date = snapshot['StartTime'].replace(tzinfo=None)
            
            if snapshot_date < cutoff_date:
                try:
                    self.ec2_client.delete_snapshot(
                        SnapshotId=snapshot['SnapshotId']
                    )
                    deleted_count += 1
                    logger.info(
                        f"Deleted snapshot {snapshot['SnapshotId']} "
                        f"from {snapshot_date}"
                    )
                except Exception as e:
                    logger.warning(
                        f"Could not delete snapshot "
                        f"{snapshot['SnapshotId']}: {e}"
                    )
        
        return deleted_count


# Usage Examples
if __name__ == "__main__":
    # Initialize manager
    manager = EC2Manager(region='us-east-1')
    
    # Example 1: List dev instances
    dev_instances = manager.list_instances_by_tag('Environment', 'dev')
    print(f"Found {len(dev_instances)} dev instances")
    
    # Example 2: Auto-stop instances
    result = manager.stop_instances_by_schedule()
    print(f"Stopped: {result['stopped']}, Failed: {result['failed']}")
    
    # Example 3: Create backup
    backup = manager.create_ami_backup('i-1234567890abcdef0')
    print(f"Created backup: {backup['ami_id']}")
    
    # Example 4: Cleanup old snapshots
    deleted = manager.cleanup_old_snapshots(retention_days=30)
    print(f"Deleted {deleted} old snapshots")
```

---

## 3. Kubernetes Automation Examples

### Example: Pod Health Monitoring

```python
"""
pod_health_checker.py

Monitor Kubernetes pod health using simple functions.
No classes - just straightforward, easy-to-understand functions.

Common Interview Question:
"How would you detect and auto-remediate unhealthy pods in production?"

Production Use Cases:
- Automated health checks across namespaces
- Crash loop detection and alerting
- Resource exhaustion monitoring
- Auto-restart of failing pods

Prerequisites:
- kubernetes client installed: pip install kubernetes
- kubeconfig file with cluster access
- Appropriate RBAC permissions
"""

from kubernetes import client, config
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_kubernetes_client(kubeconfig_path: Optional[str] = None):
    """
    Initialize Kubernetes client configuration.
    
    This function sets up the Kubernetes Python client to talk to your cluster.
    It tries different methods in order:
    1. If kubeconfig_path provided, use that file
    2. If running inside a pod, use in-cluster config
    3. Otherwise, use default kubeconfig (~/.kube/config)
    
    Args:
        kubeconfig_path: Optional path to kubeconfig file
        
    Returns:
        CoreV1Api client object for pod operations
        
    Why this matters:
        - In development: Uses your local kubectl config
        - In production (pod): Automatically uses service account
        - Flexible: Can specify different clusters
        
    Interview Tip:
        Q: How do you authenticate to Kubernetes from code?
        A: Service accounts (in cluster) or kubeconfig (external).
           Always use service accounts in production for security.
    """
    # Try to load configuration
    if kubeconfig_path:
        # Load from specific file path
        config.load_kube_config(config_file=kubeconfig_path)
        logger.info(f"Loaded kubeconfig from {kubeconfig_path}")
    else:
        try:
            # Try in-cluster config first (when running in a pod)
            # This uses the service account mounted at /var/run/secrets/kubernetes.io/
            config.load_incluster_config()
            logger.info("Loaded in-cluster configuration")
        except config.ConfigException:
            # Fall back to default kubeconfig (~/.kube/config)
            config.load_kube_config()
            logger.info("Loaded default kubeconfig")
    
    # Return a CoreV1Api client for working with pods, services, etc.
    return client.CoreV1Api()


def find_crashlooping_pods(namespace: str = 'default', restart_threshold: int = 5) -> List[Dict]:
    """
    Find all pods that are crash looping (restarting repeatedly).
    
    What is a crash loop?
    A crash loop happens when:
    1. Pod starts
    2. Container crashes (exits with error)
    3. Kubernetes restarts it (exponential backoff)
    4. Repeat...
    
    Common causes:
    - Application bugs
    - Missing configuration
    - Failed health checks
    - Out of memory
    - Database connection failures
    
    Args:
        namespace: Kubernetes namespace to check (default: default)
        restart_threshold: How many restarts before flagging (default: 5)
        
    Returns:
        List of dictionaries, each containing:
        - pod_name: Name of the problematic pod
        - namespace: Which namespace it's in
        - container_name: Which container is crashing
        - restart_count: How many times it's restarted
        - current_state: Current container state
        - last_termination_reason: Why it crashed last time
        
    Example:
        # Find all crashlooping pods in production namespace
        problems = find_crashlooping_pods(namespace='production', restart_threshold=3)
        for pod in problems:
            print(f"ALERT: {pod['pod_name']} has restarted {pod['restart_count']} times!")
            print(f"Reason: {pod['last_termination_reason']}")
    
    Interview Scenario:
        Q: "Write a script to find all crash-looping pods"
        A: This is the solution! In production, you'd:
           1. Run this on a schedule (CronJob)
           2. Send alerts to PagerDuty/Slack
           3. Potentially auto-restart deployment
           4. Log to monitoring system
    """
    # Initialize Kubernetes client
    v1 = init_kubernetes_client()
    
    logger.info(f"Checking for crashlooping pods in namespace '{namespace}'")
    
    # Get all pods in the namespace
    # This returns a V1PodList object with a list of V1Pod objects
    pods = v1.list_namespaced_pod(namespace=namespace)
    
    # List to store problematic pods
    crashlooping_pods = []
    
    # Loop through each pod
    for pod in pods.items:
        # Each pod can have multiple containers
        # Check each container's status
        container_statuses = pod.status.container_statuses or []
        
        for container_status in container_statuses:
            # Get the restart count for this container
            restart_count = container_status.restart_count
            
            # Check if restarts exceed our threshold
            if restart_count >= restart_threshold:
                # Get information about why it last crashed
                last_state = container_status.last_state
                termination_reason = "Unknown"
                
                # If container was terminated, get the reason
                if last_state.terminated:
                    termination_reason = last_state.terminated.reason
                    # Also available: last_state.terminated.exit_code
                    # Also available: last_state.terminated.message
                
                # Build a dictionary with all relevant info
                pod_info = {
                    'pod_name': pod.metadata.name,
                    'namespace': pod.metadata.namespace,
                    'container_name': container_status.name,
                    'restart_count': restart_count,
                    # Current state can be: running, waiting, terminated
                    'current_state': str(container_status.state),
                    'last_termination_reason': termination_reason,
                    'pod_ip': pod.status.pod_ip,
                    'node_name': pod.spec.node_name,
                    # When the pod was created
                    'created_at': pod.metadata.creation_timestamp
                }
                
                crashlooping_pods.append(pod_info)
                
                logger.warning(
                    f"Found crashlooping pod: {pod.metadata.name}, "
                    f"container: {container_status.name}, "
                    f"restarts: {restart_count}"
                )
    
    logger.info(f"Found {len(crashlooping_pods)} crashlooping pods")
    return crashlooping_pods


def get_pod_logs(pod_name: str, namespace: str = 'default', 
                 container: Optional[str] = None, tail_lines: int = 100,
                 previous: bool = False) -> str:
    """
    Get logs from a Kubernetes pod.
    
    Why get logs?
    - Troubleshoot why a pod is failing
    - See application errors
    - Debug crash loops
    
    Args:
        pod_name: Name of the pod
        namespace: Kubernetes namespace (default: default)
        container: Specific container name (needed for multi-container pods)
        tail_lines: How many lines to get from end of log (default: 100)
        previous: Get logs from previous container instance? (default: False)
                 Use True to see why a container crashed
        
    Returns:
        Log contents as a string
        
    Example:
        # Get last 50 lines of logs from crashed container
        logs = get_pod_logs(
            pod_name='my-app-abc123',
            namespace='production',
            tail_lines=50,
            previous=True  # Get logs from crashed container
        )
        print(logs)
        
        # Look for errors
        if 'OutOfMemoryError' in logs:
            print("Pod crashed due to OOM!")
    
    Interview Question:
        Q: How do you troubleshoot a crashing pod?
        A: 
        1. Check pod status: kubectl get pod
        2. Check events: kubectl describe pod
        3. Check logs: kubectl logs (or this function with previous=True)
        4. Check resource limits
        5. Check liveness/readiness probes
    """
    # Initialize Kubernetes client
    v1 = init_kubernetes_client()
    
    logger.info(f"Getting logs for pod {pod_name}")
    
    try:
        # Call Kubernetes API to get pod logs
        # pretty='false' means no extra formatting
        # timestamps=False means no timestamp prefix
        logs = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
            previous=previous,  # Get logs from previous container if crashed
            timestamps=False
        )
        
        logger.info(f"Retrieved {len(logs.splitlines())} lines of logs")
        return logs
    
    except Exception as e:
        # Common errors:
        # - Pod doesn't exist
        # - Container name wrong
        # - No previous container (if previous=True)
        error_msg = f"Failed to get logs for {pod_name}: {e}"
        logger.error(error_msg)
        return error_msg


def restart_deployment(deployment_name: str, namespace: str = 'default') -> bool:
    """
    Perform a rolling restart of a Kubernetes deployment.
    
    What is a rolling restart?
    - Kubernetes gracefully restarts all pods in a deployment
    - Old pods stay running until new ones are ready
    - Zero downtime
    - Useful for: applying config changes, clearing bad state, forced redeploy
    
    How it works:
    We add/update an annotation on the deployment's pod template.
    This makes Kubernetes think the template changed, triggering a rollout.
    
    Args:
        deployment_name: Name of the deployment to restart
        namespace: Kubernetes namespace (default: default)
        
    Returns:
        True if successful, False otherwise
        
    Example:
        # Restart a deployment
        success = restart_deployment('my-api', namespace='production')
        if success:
            print("Restart initiated - pods will restart one by one")
        else:
            print("Restart failed")
    
    Interview Question:
        Q: How do you perform a zero-downtime restart in Kubernetes?
        A: This function! By patching the deployment template with a new
           annotation, Kubernetes initiates a rolling update. Old pods stay
           running until new pods pass health checks.
    """
    # Initialize Kubernetes client for apps (deployments, statefulsets, etc.)
    apps_v1 = client.AppsV1Api()
    
    logger.info(f"Initiating rolling restart for deployment {deployment_name}")
    
    try:
        # Get current timestamp to use as annotation value
        # This ensures the annotation is always unique
        restart_time = datetime.utcnow().isoformat() + "Z"
        
        # Build the patch to apply to the deployment
        # We're adding/updating an annotation in the pod template
        # Changing pod template triggers a rollout
        patch_body = {
            'spec': {
                'template': {
                    'metadata': {
                        'annotations': {
                            # kubectl uses this same annotation for rollout restart
                            'kubectl.kubernetes.io/restartedAt': restart_time
                        }
                    }
                }
            }
        }
        
        # Apply the patch to the deployment
        # This is equivalent to: kubectl rollout restart deployment/my-app
        apps_v1.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=patch_body
        )
        
        logger.info(f"✓ Rolling restart initiated for {deployment_name}")
        logger.info(f"  Pods will restart one by one to maintain availability")
        logger.info(f"  Monitor with: kubectl rollout status deployment/{deployment_name}")
        
        return True
    
    except Exception as e:
        # Common errors:
        # - Deployment doesn't exist
        # - Insufficient permissions
        logger.error(f"✗ Failed to restart deployment {deployment_name}: {e}")
        return False


def get_pod_resource_usage(namespace: str = 'default') -> List[Dict]:
    """
    Get CPU and memory usage for all pods in a namespace.
    
    IMPORTANT: This requires metrics-server to be installed in your cluster.
    Install with: kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    Why monitor resource usage?
    - Identify resource-hungry pods
    - Detect memory leaks
    - Right-size resource requests/limits
    - Capacity planning
    
    Args:
        namespace: Kubernetes namespace to check (default: default)
        
    Returns:
        List of dictionaries with resource usage:
        - pod_name: Name of the pod
        - containers: List of container resource usage
          - name: Container name
          - cpu_usage: CPU usage (e.g., "50m" = 50 millicores = 0.05 cores)
          - memory_usage: Memory usage (e.g., "128Mi" = 128 megabytes)
        
    Example:
        # Get resource usage for all pods
        usage = get_pod_resource_usage(namespace='production')
        for pod in usage:
            print(f"\nPod: {pod['pod_name']}")
            for container in pod['containers']:
                print(f"  {container['name']}: CPU={container['cpu']}, Memory={container['memory']}")
                
        # Find high CPU users
        high_cpu_pods = [p for p in usage if any('m' in c['cpu'] and int(c['cpu'].rstrip('m')) > 500 for c in p['containers'])]
    
    Interview Question:
        Q: How do you monitor pod resource consumption?
        A: 
        1. Metrics server (this function)
        2. Prometheus with node-exporter
        3. Cloud provider monitoring (CloudWatch, Stackdriver)
        4. Compare against requests/limits
    """
    # Initialize custom objects API for metrics
    custom_api = client.CustomObjectsApi()
    
    logger.info(f"Getting resource metrics for namespace '{namespace}'")
    
    try:
        # Query the metrics.k8s.io API
        # This is provided by metrics-server
        metrics = custom_api.list_namespaced_custom_object(
            group="metrics.k8s.io",
            version="v1beta1",
            namespace=namespace,
            plural="pods"
        )
        
        # Parse the metrics response
        pod_metrics = []
        
        for pod_metric in metrics.get('items', []):
            # Extract pod name
            pod_name = pod_metric['metadata']['name']
            
            # Extract container metrics
            containers = []
            for container in pod_metric.get('containers', []):
                containers.append({
                    'name': container['name'],
                    # CPU is in nanocores, displayed as millicores (m) or cores
                    # Example: "50m" = 50 millicores = 0.05 cores
                    'cpu': container['usage']['cpu'],
                    # Memory is in bytes, displayed with unit (Ki, Mi, Gi)
                    # Example: "128Mi" = 128 megabytes
                    'memory': container['usage']['memory']
                })
            
            pod_metrics.append({
                'pod_name': pod_name,
                'containers': containers,
                # Include timestamp of metrics
                'timestamp': pod_metric['timestamp']
            })
        
        logger.info(f"Retrieved metrics for {len(pod_metrics)} pods")
        return pod_metrics
    
    except Exception as e:
        # Common error: metrics-server not installed
        logger.error(f"Failed to get metrics: {e}")
        logger.error("Make sure metrics-server is installed in your cluster")
        return []


# Usage Examples
if __name__ == "__main__":
    print("Kubernetes Pod Monitoring Examples")
    print("=" * 60)
    
    # Example 1: Find crashlooping pods
    print("\nExample 1: Finding crashlooping pods")
    print("-" * 60)
    crashlooping = find_crashlooping_pods(namespace='default', restart_threshold=3)
    if crashlooping:
        print(f"⚠️  Found {len(crashlooping)} crashlooping pods:")
        for pod in crashlooping:
            print(f"  - {pod['pod_name']} (container: {pod['container_name']})")
            print(f"    Restarts: {pod['restart_count']}")
            print(f"    Last crash reason: {pod['last_termination_reason']}")
    else:
        print("✓ No crashlooping pods found")
    
    # Example 2: Get logs from a failing pod
    print("\nExample 2: Getting logs from a pod")
    print("-" * 60)
    # Replace with your actual pod name
    # logs = get_pod_logs(
    #     pod_name='my-app-abc123',
    #     namespace='default',
    #     tail_lines=20,
    #     previous=True  # Get logs from crashed container
    # )
    # print(logs)
    print("(Commented out - replace with your pod name to test)")
    
    # Example 3: Restart a deployment
    print("\nExample 3: Restarting a deployment")
    print("-" * 60)
    # Replace with your actual deployment name
    # success = restart_deployment('my-api', namespace='default')
    # if success:
    #     print("✓ Deployment restart initiated")
    # else:
    #     print("✗ Deployment restart failed")
    print("(Commented out - replace with your deployment name to test)")
    
    # Example 4: Get resource usage
    print("\nExample 4: Getting pod resource usage")
    print("-" * 60)
    # usage = get_pod_resource_usage(namespace='default')
    # for pod in usage:
    #     print(f"\n{pod['pod_name']}:")
    #     for container in pod['containers']:
    #         print(f"  {container['name']}: CPU={container['cpu']}, Memory={container['memory']}")
    print("(Commented out - requires metrics-server installed)")
```
    """
    Monitors pod health and provides remediation capabilities.
    
    Interview Topics:
    - Kubernetes architecture
    - Pod lifecycle
    - Troubleshooting patterns
    """
    
    def __init__(self, namespace: str = 'default', kubeconfig: Optional[str] = None):
        """
        Initialize Kubernetes client.
        
        Args:
            namespace: Kubernetes namespace to monitor
            kubeconfig: Path to kubeconfig file (None for in-cluster)
        """
        if kubeconfig:
            config.load_kube_config(config_file=kubeconfig)
        else:
            try:
                config.load_incluster_config()
            except config.ConfigException:
                config.load_kube_config()
        
        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.namespace = namespace
    
    def find_crashlooping_pods(self, threshold: int = 5) -> List[Dict]:
        """
        Identify pods in crash loop backoff state.
        
        Common Interview Question:
        "Write a script to find all crash-looping pods"
        
        Args:
            threshold: Restart count threshold
        
        Returns:
            List of problematic pods with details
        """
        pods = self.v1.list_namespaced_pod(self.namespace)
        
        crashlooping_pods = []
        
        for pod in pods.items:
            for container_status in pod.status.container_statuses or []:
                restart_count = container_status.restart_count
                
                if restart_count >= threshold:
                    # Get last termination reason
                    last_state = container_status.last_state
                    termination_reason = None
                    
                    if last_state.terminated:
                        termination_reason = last_state.terminated.reason
                    
                    crashlooping_pods.append({
                        'pod_name': pod.metadata.name,
                        'namespace': pod.metadata.namespace,
                        'container_name': container_status.name,
                        'restart_count': restart_count,
                        'current_state': container_status.state,
                        'termination_reason': termination_reason,
                        'pod_ip': pod.status.pod_ip,
                        'node_name': pod.spec.node_name
                    })
        
        return crashlooping_pods
    
    def get_pod_resource_usage(self, pod_name: str) -> Dict:
        """
        Get resource usage for a pod.
        
        Interview Question:
        "How do you monitor pod resource consumption?"
        
        Returns:
            Dictionary with CPU and memory usage
        """
        # Note: Requires metrics-server to be installed
        try:
            from kubernetes import custom_objects_api
            custom_api = custom_objects_api.CustomObjectsApi()
            
            metrics = custom_api.get_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace=self.namespace,
                plural="pods",
                name=pod_name
            )
            
            containers = []
            for container in metrics['containers']:
                containers.append({
                    'name': container['name'],
                    'cpu_usage': container['usage']['cpu'],
                    'memory_usage': container['usage']['memory']
                })
            
            return {
                'pod_name': pod_name,
                'timestamp': metrics['timestamp'],
                'containers': containers
            }
        
        except Exception as e:
            logger.error(f"Failed to get metrics for {pod_name}: {e}")
            return {}
    
    def watch_pod_events(self, timeout_seconds: int = 60):
        """
        Watch pod events in real-time.
        
        Interview Scenario:
        "Implement a pod event watcher for debugging"
        
        Args:
            timeout_seconds: How long to watch events
        """
        w = watch.Watch()
        
        try:
            for event in w.stream(
                self.v1.list_namespaced_pod,
                namespace=self.namespace,
                timeout_seconds=timeout_seconds
            ):
                event_type = event['type']
                pod = event['object']
                
                logger.info(
                    f"Event: {event_type} | "
                    f"Pod: {pod.metadata.name} | "
                    f"Phase: {pod.status.phase}"
                )
                
                # Check for problematic states
                if pod.status.phase == 'Failed':
                    self._handle_failed_pod(pod)
                
        except Exception as e:
            logger.error(f"Error watching pod events: {e}")
        finally:
            w.stop()
    
    def _handle_failed_pod(self, pod):
        """Handle failed pod - log details and optionally restart."""
        logger.error(
            f"Pod {pod.metadata.name} failed. "
            f"Reason: {pod.status.reason}, "
            f"Message: {pod.status.message}"
        )
        
        # Could implement auto-remediation here
        # Example: Delete pod to trigger recreation by deployment
    
    def restart_deployment(self, deployment_name: str) -> bool:
        """
        Perform rolling restart of a deployment.
        
        Interview Question:
        "How do you perform a zero-downtime restart?"
        
        Args:
            deployment_name: Name of deployment to restart
        
        Returns:
            True if successful
        """
        try:
            # Patch deployment to trigger restart
            now = datetime.utcnow()
            now_str = now.isoformat() + "Z"
            
            body = {
                'spec': {
                    'template': {
                        'metadata': {
                            'annotations': {
                                'kubectl.kubernetes.io/restartedAt': now_str
                            }
                        }
                    }
                }
            }
            
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name,
                namespace=self.namespace,
                body=body
            )
            
            logger.info(f"Initiated rolling restart for {deployment_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to restart deployment: {e}")
            return False
    
    def get_pod_logs(
        self,
        pod_name: str,
        container: Optional[str] = None,
        tail_lines: int = 100,
        previous: bool = False
    ) -> str:
        """
        Retrieve pod logs.
        
        Interview Question:
        "How do you troubleshoot a crashing pod?"
        
        Args:
            pod_name: Name of the pod
            container: Specific container (if multi-container pod)
            tail_lines: Number of lines to retrieve
            previous: Get logs from previous container instance
        
        Returns:
            Log contents as string
        """
        try:
            logs = self.v1.read_namespaced_pod_log(
                name=pod_name,
                namespace=self.namespace,
                container=container,
                tail_lines=tail_lines,
                previous=previous
            )
            return logs
        
        except Exception as e:
            logger.error(f"Failed to get logs for {pod_name}: {e}")
            return ""


# Usage Examples
if __name__ == "__main__":
    # Initialize monitor
    monitor = PodHealthMonitor(namespace='production')
    
    # Example 1: Find crashlooping pods
    crashlooping = monitor.find_crashlooping_pods(threshold=5)
    for pod in crashlooping:
        print(f"Crashlooping: {pod['pod_name']} - "
              f"Restarts: {pod['restart_count']}")
    
    # Example 2: Get pod logs for debugging
    logs = monitor.get_pod_logs('my-app-pod', tail_lines=50)
    print(logs)
    
    # Example 3: Watch pod events
    print("Watching pod events for 60 seconds...")
    monitor.watch_pod_events(timeout_seconds=60)
    
    # Example 4: Restart deployment
    success = monitor.restart_deployment('my-app-deployment')
    print(f"Deployment restart: {'Success' if success else 'Failed'}")
```

---

## 4. HashiCorp Vault Integration

### Example: Secret Management

```python
"""
vault_client.py

HashiCorp Vault integration for secret management.

Interview Topics:
- Secret management best practices
- Zero-trust security
- Dynamic secrets
- Secret rotation strategies
"""

import hvac
from typing import Dict, Optional, List
import logging
import os

logger = logging.getLogger(__name__)


class VaultClient:
    """
    Wrapper for HashiCorp Vault operations.
    
    Interview Questions:
        Q: How do you manage secrets in a microservices architecture?
        A: Centralized secret management with Vault, dynamic secrets,
           short-lived tokens, audit logging, encryption as a service
        
        Q: Explain secret rotation strategy
        A: Automated rotation, grace period with dual validity,
           notification to dependent services, fallback mechanisms
    """
    
    def __init__(
        self,
        vault_url: str = None,
        token: str = None,
        role_id: str = None,
        secret_id: str = None
    ):
        """
        Initialize Vault client with authentication.
        
        Supports multiple auth methods:
        - Token auth (for development)
        - AppRole auth (for production)
        
        Args:
            vault_url: Vault server URL
            token: Vault token (for token auth)
            role_id: AppRole role ID
            secret_id: AppRole secret ID
        """
        self.vault_url = vault_url or os.getenv('VAULT_ADDR')
        
        if not self.vault_url:
            raise ValueError("Vault URL must be provided")
        
        self.client = hvac.Client(url=self.vault_url)
        
        # Authenticate
        if token:
            self.client.token = token
        elif role_id and secret_id:
            self._approle_login(role_id, secret_id)
        else:
            raise ValueError("Must provide either token or AppRole credentials")
        
        if not self.client.is_authenticated():
            raise Exception("Failed to authenticate with Vault")
    
    def _approle_login(self, role_id: str, secret_id: str):
        """Authenticate using AppRole."""
        try:
            response = self.client.auth.approle.login(
                role_id=role_id,
                secret_id=secret_id
            )
            self.client.token = response['auth']['client_token']
            logger.info("Successfully authenticated with AppRole")
        except Exception as e:
            logger.error(f"AppRole authentication failed: {e}")
            raise
    
    def read_secret(
        self,
        path: str,
        mount_point: str = 'secret'
    ) -> Optional[Dict]:
        """
        Read a secret from Vault KV v2 engine.
        
        Interview Question:
        "How do you securely retrieve secrets in your application?"
        
        Args:
            path: Secret path (e.g., 'myapp/database')
            mount_point: KV engine mount point
        
        Returns:
            Secret data dictionary
        
        Example:
            vault = VaultClient(token='my-token')
            db_creds = vault.read_secret('myapp/database')
            password = db_creds['password']
        """
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=mount_point
            )
            return response['data']['data']
        except Exception as e:
            logger.error(f"Failed to read secret at {path}: {e}")
            return None
    
    def write_secret(
        self,
        path: str,
        secret_data: Dict,
        mount_point: str = 'secret'
    ) -> bool:
        """
        Write a secret to Vault KV v2 engine.
        
        Args:
            path: Secret path
            secret_data: Dictionary of secret key-value pairs
            mount_point: KV engine mount point
        
        Returns:
            True if successful
        """
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret_data,
                mount_point=mount_point
            )
            logger.info(f"Successfully wrote secret to {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write secret to {path}: {e}")
            return False
    
    def generate_database_credentials(
        self,
        role_name: str,
        mount_point: str = 'database'
    ) -> Optional[Dict]:
        """
        Generate dynamic database credentials.
        
        Interview Scenario:
        "Implement dynamic credential generation for RDS access"
        
        Args:
            role_name: Database role name configured in Vault
            mount_point: Database secrets engine mount point
        
        Returns:
            Dictionary with username and password
        
        Example:
            creds = vault.generate_database_credentials('readonly-role')
            username = creds['username']
            password = creds['password']
            # Credentials are automatically revoked after TTL
        """
        try:
            response = self.client.secrets.database.generate_credentials(
                name=role_name,
                mount_point=mount_point
            )
            
            credentials = {
                'username': response['data']['username'],
                'password': response['data']['password'],
                'lease_id': response['lease_id'],
                'lease_duration': response['lease_duration']
            }
            
            logger.info(
                f"Generated database credentials for role {role_name}, "
                f"lease duration: {credentials['lease_duration']}s"
            )
            
            return credentials
        
        except Exception as e:
            logger.error(f"Failed to generate credentials: {e}")
            return None
    
    def rotate_secret(
        self,
        path: str,
        new_secret_data: Dict,
        grace_period_seconds: int = 300
    ) -> bool:
        """
        Rotate a secret with grace period.
        
        Interview Question:
        "Explain zero-downtime secret rotation"
        
        Strategy:
        1. Write new secret to Vault
        2. Keep old secret valid during grace period
        3. Notify dependent services
        4. Remove old secret after grace period
        
        Args:
            path: Secret path
            new_secret_data: New secret values
            grace_period_seconds: Time to keep old secret valid
        
        Returns:
            True if successful
        """
        # Implementation would involve:
        # 1. Read current secret
        # 2. Write new secret
        # 3. Schedule cleanup of old secret
        # This is a simplified example
        
        return self.write_secret(path, new_secret_data)


# Usage Examples
if __name__ == "__main__":
    # Example 1: Token-based auth (development)
    vault = VaultClient(
        vault_url='http://localhost:8200',
        token='dev-token'
    )
    
    # Example 2: AppRole auth (production)
    vault_prod = VaultClient(
        vault_url='https://vault.example.com',
        role_id=os.getenv('VAULT_ROLE_ID'),
        secret_id=os.getenv('VAULT_SECRET_ID')
    )
    
    # Example 3: Read database credentials
    db_secret = vault.read_secret('myapp/database')
    if db_secret:
        print(f"DB Password: {db_secret['password']}")
    
    # Example 4: Generate dynamic database credentials
    dynamic_creds = vault.generate_database_credentials('readonly-role')
    if dynamic_creds:
        print(f"Username: {dynamic_creds['username']}")
        print(f"Lease duration: {dynamic_creds['lease_duration']}s")
    
    # Example 5: Write new secret
    vault.write_secret(
        'myapp/api-keys',
        {
            'api_key': 'new-api-key',
            'api_secret': 'new-api-secret'
        }
    )
```

---

## Interview Question Examples for Each Module

### File: `interview_questions.md` in each directory

```markdown
# Interview Questions - [Module Name]

## Conceptual Questions

### Q1: Explain [concept] and when you would use it
**Expected Answer Points:**
- Core definition
- Use cases
- Trade-offs
- Real-world example from your experience

### Q2: Design [system/solution]
**Expected Approach:**
1. Clarify requirements
2. Discuss architecture options
3. Explain technology choices
4. Address scalability/reliability
5. Discuss monitoring and observability

## Coding Challenges

### Challenge 1: [Name]
**Problem Statement:**
[Detailed problem description]

**Example Input:**
```
[Sample input]
```

**Expected Output:**
```
[Sample output]
```

**Constraints:**
- Time complexity: O(?)
- Space complexity: O(?)

**Solution Approach:**
1. Step 1
2. Step 2
3. Step 3

**Common Pitfalls:**
- Pitfall 1
- Pitfall 2

## Behavioral Questions

### Scenario 1: [Incident/Challenge]
**Question:** Tell me about a time when [scenario]

**STAR Format:**
- **Situation:** [Context]
- **Task:** [Your responsibility]
- **Action:** [What you did]
- **Result:** [Outcome and learning]

## Technical Deep Dives

### Topic: [Technical Area]
**Interviewer might ask:**
- How does [technology] work internally?
- What are the performance characteristics?
- How do you troubleshoot [common issue]?
- What metrics do you monitor?
```

---

This guide provides production-ready, interview-focused code examples with:
✅ Proper error handling
✅ Logging
✅ Type hints
✅ Comprehensive docstrings
✅ Real-world use cases
✅ Interview questions embedded in code
✅ Best practices
✅ Security considerations

Next steps: Implement similar examples for all 15 modules!
