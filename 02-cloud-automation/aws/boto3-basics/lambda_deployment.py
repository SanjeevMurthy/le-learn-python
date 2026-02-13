"""
lambda_deployment.py

AWS Lambda function management and deployment using boto3.

Interview Topics:
- Lambda cold starts and optimization
- Lambda execution model and concurrency
- Serverless architecture trade-offs

Production Use Cases:
- Automating Lambda function deployment from CI/CD
- Creating Lambda functions for event-driven automation
- Managing Lambda versions and aliases for blue-green deploy
- Setting up Lambda triggers (S3, CloudWatch Events, API Gateway)

Prerequisites:
- boto3 (pip install boto3)
- AWS credentials with Lambda permissions
"""

import os
import json
import zipfile
import logging
from typing import Dict, Any, Optional, List
from io import BytesIO

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_lambda_client(region: str = None):
    """Create a boto3 Lambda client."""
    import boto3
    return boto3.client(
        'lambda',
        region_name=region or os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    )


def create_deployment_package(
    source_dir: str,
    output_path: Optional[str] = None
) -> bytes:
    """
    Create a ZIP deployment package from a directory.

    Lambda functions are deployed as ZIP archives containing
    the handler code and any dependencies.

    Args:
        source_dir: Directory containing Lambda handler code
        output_path: Optional path to save the ZIP file

    Returns:
        ZIP file contents as bytes

    Interview Question:
        Q: How do you package Lambda functions with dependencies?
        A: 1. Install deps to a local directory: pip install -t ./package/
           2. ZIP the package directory + your handler code
           3. For large packages (>50MB): use Lambda Layers
           4. For even larger: use container images (up to 10GB)
           5. CI/CD should automate this build process
    """
    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zf.write(file_path, arcname)

    zip_bytes = zip_buffer.getvalue()

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(zip_bytes)
        logger.info(f"Saved deployment package to {output_path} ({len(zip_bytes)} bytes)")

    logger.info(f"Created deployment package: {len(zip_bytes)} bytes")
    return zip_bytes


def create_lambda_function(
    function_name: str,
    handler: str,
    role_arn: str,
    zip_bytes: bytes,
    runtime: str = 'python3.12',
    memory_mb: int = 128,
    timeout: int = 30,
    environment: Optional[Dict[str, str]] = None,
    description: str = '',
    region: str = None
) -> Dict[str, Any]:
    """
    Create a new Lambda function.

    Args:
        function_name: Name for the Lambda function
        handler: Handler entry point (e.g., 'handler.lambda_handler')
        role_arn: IAM role ARN for the function's execution role
        zip_bytes: Deployment package as bytes
        runtime: Lambda runtime (e.g., 'python3.12')
        memory_mb: Memory allocation in MB (128-10240)
        timeout: Function timeout in seconds (max 900 = 15 mins)
        environment: Environment variables
        description: Function description
        region: AWS region

    Returns:
        Function creation details

    Interview Question:
        Q: How does Lambda cold start work and how do you optimize it?
        A: Cold start occurs when Lambda creates a new execution environment:
           1. Download your code/container
           2. Initialize the runtime
           3. Run initialization code (outside handler)
           Optimizations:
           - Keep deployment packages small
           - Initialize SDK clients outside the handler
           - Use provisioned concurrency for latency-sensitive functions
           - Choose a fast runtime (Python/Node over Java/C#)
           - Use Lambda SnapStart (Java) or reserved concurrency
    """
    client = get_lambda_client(region)

    function_config = {
        'FunctionName': function_name,
        'Runtime': runtime,
        'Role': role_arn,
        'Handler': handler,
        'Code': {'ZipFile': zip_bytes},
        'Description': description,
        'Timeout': timeout,
        'MemorySize': memory_mb,
        'Publish': True,
        'Tags': {
            'ManagedBy': 'devops-toolkit',
            'Runtime': runtime,
        }
    }

    if environment:
        function_config['Environment'] = {'Variables': environment}

    try:
        response = client.create_function(**function_config)
        logger.info(
            f"Created Lambda function: {function_name} "
            f"(ARN: {response['FunctionArn']})"
        )
        return {
            'function_name': response['FunctionName'],
            'function_arn': response['FunctionArn'],
            'runtime': response['Runtime'],
            'memory': response['MemorySize'],
            'timeout': response['Timeout'],
            'version': response['Version'],
            'status': 'created'
        }

    except Exception as e:
        logger.error(f"Failed to create Lambda function: {e}")
        return {'function_name': function_name, 'status': 'error', 'error': str(e)}


def update_lambda_function(
    function_name: str,
    zip_bytes: bytes,
    publish: bool = True,
    region: str = None
) -> Dict[str, Any]:
    """
    Update a Lambda function's code.

    Args:
        function_name: Name of the function to update
        zip_bytes: New deployment package
        publish: Whether to publish a new version
        region: AWS region

    Returns:
        Update result details
    """
    client = get_lambda_client(region)

    try:
        response = client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_bytes,
            Publish=publish
        )

        logger.info(
            f"Updated Lambda: {function_name} → version {response.get('Version', 'N/A')}"
        )
        return {
            'function_name': response['FunctionName'],
            'version': response.get('Version', '$LATEST'),
            'code_sha256': response['CodeSha256'],
            'code_size': response['CodeSize'],
            'status': 'updated'
        }

    except Exception as e:
        logger.error(f"Failed to update Lambda: {e}")
        return {'function_name': function_name, 'status': 'error', 'error': str(e)}


def invoke_lambda(
    function_name: str,
    payload: Dict[str, Any],
    invocation_type: str = 'RequestResponse',
    region: str = None
) -> Dict[str, Any]:
    """
    Invoke a Lambda function synchronously or asynchronously.

    Args:
        function_name: Lambda function name or ARN
        payload: JSON payload to send
        invocation_type: 'RequestResponse' (sync) or 'Event' (async)
        region: AWS region

    Returns:
        Invocation result

    Interview Question:
        Q: Explain Lambda concurrency models.
        A: - Unreserved: shares account-level concurrency (default 1000)
           - Reserved: guarantees N concurrent executions for this function
           - Provisioned: pre-initializes N execution environments
             (eliminates cold starts, costs more)
           Use reserved for critical functions that shouldn't be throttled.
           Use provisioned for latency-sensitive APIs.
    """
    client = get_lambda_client(region)

    try:
        response = client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            Payload=json.dumps(payload)
        )

        result = {
            'function_name': function_name,
            'status_code': response['StatusCode'],
            'invocation_type': invocation_type,
        }

        if invocation_type == 'RequestResponse':
            response_payload = json.loads(response['Payload'].read())
            result['response'] = response_payload

        if 'FunctionError' in response:
            result['error'] = response['FunctionError']

        return result

    except Exception as e:
        logger.error(f"Lambda invocation failed: {e}")
        return {'function_name': function_name, 'status': 'error', 'error': str(e)}


def list_lambda_functions(region: str = None) -> List[Dict[str, Any]]:
    """
    List all Lambda functions in the account/region.

    Returns:
        List of function summaries
    """
    client = get_lambda_client(region)
    functions = []

    paginator = client.get_paginator('list_functions')
    for page in paginator.paginate():
        for func in page['Functions']:
            functions.append({
                'function_name': func['FunctionName'],
                'runtime': func.get('Runtime', 'N/A'),
                'memory': func['MemorySize'],
                'timeout': func['Timeout'],
                'code_size': func['CodeSize'],
                'last_modified': func['LastModified'],
                'handler': func.get('Handler', 'N/A'),
            })

    logger.info(f"Found {len(functions)} Lambda functions")
    return functions


# ============================================================
# Usage Examples
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Lambda Deployment — Usage Examples")
    print("=" * 60)
    print("""
    NOTE: These examples require valid AWS credentials with Lambda permissions.

    Example usage (uncomment to run):

    # List all functions
    functions = list_lambda_functions()
    for f in functions:
        print(f"  {f['function_name']}: {f['runtime']}, {f['memory']}MB")

    # Create deployment package
    zip_bytes = create_deployment_package('./my_function/')

    # Create Lambda function
    result = create_lambda_function(
        function_name='my-auto-remediation',
        handler='handler.lambda_handler',
        role_arn='arn:aws:iam::123456789012:role/lambda-exec-role',
        zip_bytes=zip_bytes,
        memory_mb=256,
        timeout=60,
        environment={'SLACK_WEBHOOK': 'https://hooks.slack.com/...'}
    )

    # Invoke function
    result = invoke_lambda(
        'my-auto-remediation',
        payload={'action': 'check_health', 'targets': ['web-1', 'web-2']}
    )
    """)
