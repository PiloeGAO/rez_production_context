# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest

# Run a single test file or test
uv run pytest tests/test_markers.py
uv run pytest tests/test_markers.py::test_name

# Format code
uv run black src tests

# Sort imports
uv run isort src tests

# Lint
uv run ruff check src tests

# Install optional backends for testing
uv sync --extra kitsu
uv sync --extra shotgun
```

Test markers: `@pytest.mark.gazu_only` and `@pytest.mark.shotgun_only` automatically skip if the corresponding backend isn't installed.

## Architecture

This library provides a unified abstraction over VFX production management systems (Kitsu, Shotgrid/Flow) for use in Rez resolver pipelines.

### Connector pattern (`src/rez_production_context/connectors/`)

- `base.py` — Abstract base class defining the connector interface. All retrieval methods are `@classmethod`s (stateless).
- `kitsu.py` / `shotgun.py` — Concrete implementations. Each checks its own availability at import time via `importlib`. Only available connectors are registered.
- `__init__.py` — Builds the `CONNECTORS` list by instantiating only connectors whose optional dependency is installed.

To add a new backend: subclass `Base`, implement the abstract methods, add it to `__init__.py`.

### Context models (`src/rez_production_context/contexts.py`)

Dataclass-like hierarchy: `Studio → Project → (AssetType → Asset) | (Sequence → Shot)`. Properties use private name-mangled attributes for read-only access.

### Manager (`src/rez_production_context/manager.py`)

Thread-safe singleton (via `SingletonMeta` metaclass). Reads an INI config file whose path comes from the `RESOLVER_CONTEXT_CONFIG` environment variable. Validates that exactly one connector section is present, then instantiates that connector.

**Config file format:**
```ini
[DEFAULT]
cache = yes

[KITSU]
url = http://localhost:8080
api_key = 4p1...k3y
```

### Utils (`src/rez_production_context/utils.py`)

`NoInheritInstanceCheck` — metaclass that makes `isinstance()` return `True` only for exact type matches, not subclasses.