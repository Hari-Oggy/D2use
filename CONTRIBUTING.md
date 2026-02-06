# Contributing to ML Dataset Factory

Thank you for considering contributing to ML Dataset Factory! This document provides guidelines and instructions for contributing.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [How to Contribute](#how-to-contribute)
5. [Pull Request Process](#pull-request-process)
6. [Coding Standards](#coding-standards)
7. [Testing Guidelines](#testing-guidelines)
8. [Documentation](#documentation)

---

## Code of Conduct

This project follows a Code of Conduct. By participating, you agree to uphold a welcoming and inclusive environment.

---

## Getting Started

### Prerequisites

- Python 3.11+
- uv package manager
- Git
- LM Studio (optional, for AI features)

### Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork:
git clone https://github.com/YOUR_USERNAME/D2use.git
cd D2use

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/D2use.git
```

---

## Development Setup

### 1. Install Dependencies

```bash
uv sync --dev
```

### 2. Create Environment File

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Install Pre-commit Hooks (Optional)

```bash
uv run pre-commit install
```

### 4. Verify Setup

```bash
uv run pytest tests/ -v
```

---

## How to Contribute

### Types of Contributions

1. **Bug Fixes**: Fix issues reported in GitHub Issues
2. **Features**: Implement new features from roadmap or proposals
3. **Documentation**: Improve docs, add examples
4. **Tests**: Add test coverage
5. **Performance**: Optimize existing code

### Before You Start

1. Check existing issues to avoid duplicates
2. For new features, open an issue first to discuss
3. Assign yourself to the issue you're working on

---

## Pull Request Process

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes

- Write clean, documented code
- Add tests for new functionality
- Update documentation if needed

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest tests/ -v

# Check specific module
uv run pytest tests/test_your_module.py -v

# Verify imports
uv run python -c "from src.your_module import YourClass; print('OK')"
```

### 4. Commit Your Changes

```bash
git add .
git commit -m "feat: add your feature description"
```

**Commit Message Format:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `test:` Adding tests
- `refactor:` Code refactoring
- `perf:` Performance improvement

### 5. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

### 6. PR Review

- Address review comments
- Keep PR focused and reasonably sized
- Update based on feedback

---

## Coding Standards

### Python Style

- **Formatter**: Black (line length 100)
- **Imports**: isort
- **Linting**: flake8

### Type Hints

```python
# Required for all public functions
def process_data(df: pl.DataFrame, max_rows: int = 1000) -> pl.DataFrame:
    """
    Process the input DataFrame.

    Args:
        df: Input DataFrame
        max_rows: Maximum rows to process

    Returns:
        Processed DataFrame
    """
    return df.head(max_rows)
```

### Docstrings

Use Google-style docstrings:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When param2 is negative
    """
    pass
```

### Error Handling

```python
# Use specific exceptions
try:
    result = risky_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise UserFriendlyError(ErrorCode.SPECIFIC_ERROR, str(e))
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate levels
logger.debug("Detailed info for debugging")
logger.info("General information")
logger.warning("Something unexpected but recoverable")
logger.error("Error occurred")
```

---

## Testing Guidelines

### Test File Naming

```
tests/
├── test_encoding_detector.py
├── test_date_parser.py
├── test_retry.py
└── test_your_module.py
```

### Test Structure

```python
import pytest

class TestYourModule:
    """Test suite for YourModule"""

    def test_basic_functionality(self):
        """Test basic case"""
        result = your_function("input")
        assert result == "expected"

    def test_edge_case(self):
        """Test edge case"""
        result = your_function("")
        assert result is None

    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async functionality"""
        result = await async_function()
        assert result == "expected"
```

### Running Tests

```bash
# All tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=html

# Specific test
uv run pytest tests/test_module.py::TestClass::test_method -v
```

---

## Documentation

### Update Documentation When

- Adding new features
- Changing API signatures
- Adding configuration options
- Fixing significant bugs

### Documentation Files

| File                              | Purpose                 |
| --------------------------------- | ----------------------- |
| `README.md`                       | Project overview        |
| `docs/GETTING_STARTED.md`         | Setup guide             |
| `docs/TECHNICAL_DOCUMENTATION.md` | Full technical docs     |
| `docs/API_KEYS.md`                | API key setup           |
| `docs/LMSTUDIO_SETUP.md`          | LM Studio configuration |

### Docstring Updates

All public functions should have complete docstrings.

---

## Questions?

- Open a GitHub Issue for questions
- Check existing documentation
- Review closed issues for solutions

---

**Thank you for contributing!** 🎉
