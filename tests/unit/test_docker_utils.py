"""
test_docker_utils.py

Unit tests for Module 01 — Docker utilities.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def test_dockerfile_parse():
    """Test basic Dockerfile instruction parsing."""
    dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
"""
    lines = [l.strip() for l in dockerfile_content.strip().split('\n') if l.strip()]
    instructions = [l.split()[0] for l in lines]
    assert 'FROM' in instructions
    assert 'COPY' in instructions
    assert 'CMD' in instructions
    print("  ✅ test_dockerfile_parse")


def test_image_tag_format():
    """Test Docker image tag formatting."""
    registry = "registry.example.com"
    image = "myapp"
    tag = "v1.2.3"
    full_tag = f"{registry}/{image}:{tag}"
    assert full_tag == "registry.example.com/myapp:v1.2.3"

    # Validate tag regex
    import re
    pattern = r'^[\w.-]+/[\w.-]+:[\w.-]+$'
    assert re.match(pattern, full_tag), "Tag should match expected format"
    print("  ✅ test_image_tag_format")


def test_port_mapping_parse():
    """Test Docker port mapping parsing."""
    mapping = "8080:80"
    host_port, container_port = mapping.split(':')
    assert host_port == "8080"
    assert container_port == "80"
    print("  ✅ test_port_mapping_parse")


if __name__ == "__main__":
    print("Docker Utils Unit Tests")
    test_dockerfile_parse()
    test_image_tag_format()
    test_port_mapping_parse()
    print("  All tests passed!")
