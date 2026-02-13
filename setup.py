"""
DevOps/SRE Python Toolkit - Package Setup

This setup.py enables installing the toolkit as a package
for easier imports across modules.
"""

from setuptools import setup, find_packages

setup(
    name="devops-sre-python-toolkit",
    version="0.1.0",
    description="Comprehensive Python toolkit for DevOps/SRE engineers",
    author="DevOps/SRE Engineer",
    python_requires=">=3.8",
    packages=find_packages(exclude=["tests*", "plan*"]),
    install_requires=[
        "requests>=2.31.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "tenacity>=8.2.0",
        "structlog>=23.1.0",
    ],
    extras_require={
        "aws": ["boto3>=1.28.0"],
        "gcp": ["google-cloud-compute>=1.14.0", "google-cloud-storage>=2.10.0"],
        "k8s": ["kubernetes>=28.0.0"],
        "monitoring": ["prometheus-client>=0.17.0"],
        "vault": ["hvac>=1.2.0"],
        "cicd": ["pygithub>=2.1.0", "python-jenkins>=1.8.0"],
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "mypy>=1.5.0",
            "flake8>=6.1.0",
        ],
    },
)
