---
name: python-project-setup
description: >
  Sets up Python projects with modern tooling including pyproject.toml, linting with ruff,
  formatting, type checking with mypy or pyright, testing with pytest, and pre-commit hooks.
  Triggers on: "setup Python project", "create Python package", "python project structure", "pyproject.toml".
license: MIT
metadata:
  author: Community
  version: 1.0.0
  category: project-setup
---

# Python Project Setup

## Instructions

### Step 1: Gather Requirements

Ask:
1. What type of project? (library/package, web app, CLI tool, data pipeline)
2. Minimum Python version? (default: 3.11+)
3. Package manager preference? (pip, uv, poetry, pdm)
4. Layout preference? (src-layout or flat-layout)
5. What frameworks? (FastAPI, Django, Flask, Click, Typer)
6. CI platform? (GitHub Actions, GitLab CI)

### Step 2: Project Structure

**src-layout (recommended for libraries):**
```
my-project/
  src/
    my_package/
      __init__.py
      main.py
      models.py
  tests/
    __init__.py
    conftest.py
    test_main.py
  pyproject.toml
  README.md
  .pre-commit-config.yaml
  .github/
    workflows/
      ci.yml
```

**flat-layout (simpler, for apps):**
```
my-project/
  my_package/
    __init__.py
    main.py
  tests/
    conftest.py
    test_main.py
  pyproject.toml
  README.md
```

Use src-layout by default. It prevents accidental imports of the source during testing.

### Step 3: Generate pyproject.toml

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-package"
version = "0.1.0"
description = "A brief description of the project"
readme = "README.md"
license = "MIT"
requires-python = ">=3.11"
authors = [
    { name = "Your Name", email = "you@example.com" },
]
dependencies = []

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "ruff>=0.4",
    "mypy>=1.10",
    "pre-commit>=3.7",
]

[project.scripts]
my-cli = "my_package.main:cli"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
]

[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
    "SIM",  # flake8-simplify
]

[tool.ruff.lint.isort]
known-first-party = ["my_package"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.coverage.run]
source = ["src/my_package"]
branch = true

[tool.coverage.report]
fail_under = 80
show_missing = true
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
]
```

### Step 4: Configure Linting and Formatting

**Ruff (recommended - replaces flake8, isort, black):**

Add to pyproject.toml (shown above). Ruff handles both linting and formatting:

```bash
# Lint
ruff check .

# Format
ruff format .

# Fix auto-fixable issues
ruff check --fix .
```

**Type checking with mypy:**
```bash
mypy src/
```

For strict mode, address these common issues:
- Add return type annotations to all functions
- Use `from __future__ import annotations` for modern syntax
- Add `py.typed` marker file for library packages

### Step 5: Testing Setup

**conftest.py with common fixtures:**
```python
import pytest


@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {"name": "test", "value": 42}


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config file."""
    config_file = tmp_path / "config.toml"
    config_file.write_text('[app]\ndebug = true\n')
    return config_file
```

**Run tests with coverage:**
```bash
pytest --cov --cov-report=term-missing --cov-report=html
```

### Step 6: Pre-commit Hooks

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.4
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.10.0
    hooks:
      - id: mypy
        additional_dependencies: []

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
```

Install: `pre-commit install`

### Step 7: Development Workflow Commands

Provide a Makefile or document these commands:

```makefile
.PHONY: install lint format test typecheck all

install:
	pip install -e ".[dev]"
	pre-commit install

lint:
	ruff check .

format:
	ruff format .

test:
	pytest --cov --cov-report=term-missing

typecheck:
	mypy src/

all: lint typecheck test
```

## Example

User says: "Set up a new Python CLI tool project"

Response:
- src-layout with Click/Typer for CLI framework
- pyproject.toml with CLI entry point in [project.scripts]
- Ruff for linting and formatting
- pytest with fixtures for CLI testing (CliRunner)
- Pre-commit config
- GitHub Actions CI workflow

## Guidelines

- Default to src-layout for libraries, flat-layout for single-purpose apps
- Always use pyproject.toml over setup.py or setup.cfg (PEP 621)
- Recommend ruff over separate flake8+isort+black installations
- Pin minimum versions in dependencies, not exact versions
- Use optional dependency groups: dev, test, docs
- Include py.typed marker for typed libraries
- Set coverage threshold at 80% minimum
- Configure strict mypy mode from the start (easier than adding later)
- Use uv for faster dependency resolution when available
