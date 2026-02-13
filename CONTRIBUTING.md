# Contributing to DevOps/SRE Python Toolkit

Thank you for your interest in contributing! This guide will help you get started.

## 📋 Code Style

- **Formatting**: Black with line length 100
- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: Google style, include interview questions where applicable
- **Imports**: Sorted with isort
- **Functions**: Prefer simple functions over classes (unless stateful API client)
- **Comments**: Extensive inline comments explaining _why_, not just _what_

## 🏗️ Adding a New Example

1. **Choose the right module** — place your example in the appropriate numbered directory
2. **Follow the file template**:

```python
"""
module_name.py

Brief description of what this module does.

Interview Topics:
- Topic 1
- Topic 2

Production Use Cases:
- Use case 1
- Use case 2

Prerequisites:
- Required packages
- Credentials needed
"""

import logging
from typing import List, Dict, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def my_function(param1: str, param2: int = 10) -> Dict:
    """
    Brief description.

    Detailed explanation of what this function does and why.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Dictionary with results

    Example:
        result = my_function('test', 5)

    Interview Question:
        Q: Related interview question
        A: Expected answer
    """
    # Step 1: Explain what we're doing
    # ...implementation...
    pass


# Usage Examples
if __name__ == "__main__":
    print("Example: Description")
    print("-" * 50)
    # result = my_function('test')
    # print(f"Result: {result}")
```

3. **Write tests** — add tests in `tests/unit/` or `tests/integration/`
4. **Update README** — update the module's README.md with your example
5. **Submit PR** with a descriptive title and explanation

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific module tests
pytest tests/unit/test_retry_decorators.py

# Run with coverage
pytest --cov=. tests/
```

## ✅ Checklist Before Submitting

- [ ] Code follows the style guide (Black, type hints, docstrings)
- [ ] Inline comments explain the _why_
- [ ] Interview questions included in docstrings
- [ ] Usage examples in `__main__` block
- [ ] Unit tests written
- [ ] Module README updated
- [ ] No credentials or secrets in code
