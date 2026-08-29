# rez-production-context

A Python library that provides a unified abstraction over VFX production management systems (Kitsu, ShotGrid/Flow Production Tracking) for use in Rez resolver pipelines.

It exposes a simple API to resolve the current production context — studio, project, asset type, asset, sequence, or shot — either from explicit string arguments or from environment variables set by the resolver.

---

## Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
  - [Kitsu](#kitsu)
  - [Flow Production Tracking (ShotGrid)](#flow-production-tracking-shotgrid)
- [Usage](#usage)
  - [Resolving a context](#resolving-a-context)
  - [Resolving from environment variables](#resolving-from-environment-variables)
  - [Context objects](#context-objects)
- [Environment variables](#environment-variables)
- [Development](#development)
  - [Running tests](#running-tests)
  - [Code quality](#code-quality)
  - [Adding a new connector](#adding-a-new-connector)

---

## Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

Optional backends (install at least one):

| Backend | Package | Extra |
|---|---|---|
| Kitsu / Zou | `gazu` | `kitsu` |
| ShotGrid / Flow | `shotgun-api3` | `shotgun` |

---

## Installation

```bash
# Core library only
uv sync

# With Kitsu support
uv sync --extra kitsu

# With ShotGrid support
uv sync --extra shotgun

# With both
uv sync --extra kitsu --extra shotgun
```

---

## Configuration

The library reads an INI config file whose path is set via the `RESOLVER_CONTEXT_CONFIG` environment variable.

```bash
export RESOLVER_CONTEXT_CONFIG=/path/to/config.ini
```

Exactly one connector section must be present. The `[DEFAULT]` section supports a `cache` flag to enable in-memory caching of all API results for the lifetime of the process.

### Kitsu

Authentication supports two modes:

**API token** (bot / service account):

```ini
[DEFAULT]
cache = yes

[KITSU]
url = http://localhost:8080
api_key = <your-api-token>
```

**Email + password** (user account):

```ini
[DEFAULT]
cache = yes

[KITSU]
url = http://localhost:8080
email = user@studio.com
api_key = <password>
```

The bot or user account requires at minimum read access to projects, asset types, assets, sequences, and shots.

### Flow Production Tracking (ShotGrid)

Script-based authentication:

```ini
[DEFAULT]
cache = yes

[SHOTGUN]
url = https://studio.shotgunstudio.com
script_name = <your-script-name>
api_key = <your-api-key>
```

The API script must have at least read access to Projects, Assets, Sequences, Shots, and their fields.

> **Note:** Asset types are not a first-class entity in ShotGrid. They are derived from the distinct `sg_asset_type` field values found on asset records.

---

## Usage

### Resolving a context

Use `get_context()` to resolve a context from string identifiers. All arguments are optional; the function returns the most specific context it can build from what is provided.

```python
from rez_production_context import get_context

# No arguments → Studio
ctx = get_context()

# Project only → Project
ctx = get_context(project="Big Buck Bunny")

# Project + category → AssetType or Sequence (auto-detected)
ctx = get_context(project="Big Buck Bunny", category="Character")   # AssetType
ctx = get_context(project="Big Buck Bunny", category="SQ010")        # Sequence

# Project + category + entity → Asset or Shot
ctx = get_context(project="Big Buck Bunny", category="Character", entity="Bunny")  # Asset
ctx = get_context(project="Big Buck Bunny", category="SQ010", entity="SH010")      # Shot

# Any level accepts an optional pipeline step
ctx = get_context(project="Big Buck Bunny", category="SQ010", entity="SH010", step="lighting")
```

### Resolving from environment variables

`get_context_from_env()` reads the same four variables set by the Rez resolver and delegates to `get_context()`:

```python
from rez_production_context import get_context_from_env

ctx = get_context_from_env()
```

| Variable | Argument |
|---|---|
| `RESOLVER_PROJECT` | `project` |
| `RESOLVER_CATEGORY` | `category` |
| `RESOLVER_ENTITY` | `entity` |
| `RESOLVER_STEP` | `step` |

All variables are optional. When none are set the result is a `Studio` context.

### Context objects

Every context object exposes a `step` property and read-only navigation properties up the hierarchy.

| Class | Properties |
|---|---|
| `Studio` | `step`, `projects` |
| `Project` | `name`, `step`, `asset_types`, `sequences` |
| `AssetType` | `name`, `step`, `project`, `assets` |
| `Asset` | `name`, `step`, `project`, `asset_type` |
| `Sequence` | `name`, `step`, `project`, `shots` |
| `Shot` | `name`, `step`, `project`, `sequence` |

The navigation properties (`projects`, `asset_types`, `assets`, `sequences`, `shots`) trigger live API calls through the active connector.

```python
ctx = get_context(project="Big Buck Bunny")

for asset_type in ctx.asset_types:
    print(asset_type.name)
    for asset in asset_type.assets:
        print(f"  {asset.name}")
```

---

## Environment variables

| Variable | Description |
|---|---|
| `RESOLVER_CONTEXT_CONFIG` | **Required.** Path to the INI config file. |
| `RESOLVER_PROJECT` | Project name (read by `get_context_from_env`). |
| `RESOLVER_CATEGORY` | Asset type or sequence name (read by `get_context_from_env`). |
| `RESOLVER_ENTITY` | Asset or shot name (read by `get_context_from_env`). |
| `RESOLVER_STEP` | Pipeline step name (read by `get_context_from_env`). |

---

## Development

### Running tests

The test suite is split into **unit tests** (no backend required, always fast) and **integration tests** (require a live backend).

```
tests/
  tests_connectors/     ← unit tests
  tests_contexts.py
  tests_init.py
  tests_manager.py
  integration/
    tests_connectors/   ← integration tests (Kitsu, ShotGrid)
    docker-compose.yml  ← Zou/Kitsu Docker stack
```

**Unit tests only** (default, no backend needed):

```bash
uv run pytest -m "not integration"
```

**Integration tests only:**

```bash
uv run pytest tests/integration/
```

**All tests:**

```bash
uv run pytest
```

**Kitsu integration tests** require a running Zou instance via Docker:

```bash
uv sync --extra kitsu
uv run pytest tests/integration/ -m gazu_only
```

**ShotGrid integration tests** require ShotGrid credentials:

```bash
uv sync --extra shotgun
uv run pytest tests/integration/ -m shotgun_only
```

Set the following in a `.env` file or your environment:

```bash
SHOTGUN_SERVER_URL=https://studio.shotgunstudio.com
SHOTGUN_SCRIPT_NAME=<script-name>
SHOTGUN_API_KEY=<api-key>
```

### Code quality

```bash
# Format
uv run black src tests

# Sort imports
uv run isort src tests

# Lint
uv run ruff check src tests

# Type check
uv run mypy src
```

### Adding a new connector

1. Create `src/rez_production_context/connectors/<name>.py` and subclass `Base`:

```python
from .base import Base, EntityNotFoundError
from ..contexts import Project  # etc.

class MyConnector(Base):
    def __init__(self, url: str, api_key: str, **kwargs):
        super().__init__(**kwargs)
        # set up connection ...

    @staticmethod
    def available() -> bool:
        try:
            import importlib
            importlib.import_module("my_backend_library")
            return True
        except ImportError:
            return False

    def get_project(self, project_name: str) -> Project:
        # ...
```

2. Register it in `src/rez_production_context/connectors/__init__.py`:

```python
_CONNECTOR_REGISTRY: list[tuple[str, str]] = [
    (".kitsu", "Kitsu"),
    (".shotgun", "Shotgun"),
    (".myconnector", "MyConnector"),  # add this line
]
```

3. Add the optional dependency to `pyproject.toml`:

```toml
[project.optional-dependencies]
mybackend = ["my-backend-library>=1.0.0"]
```