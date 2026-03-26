# conftest.py
import pytest
import importlib


def _module_available(module_name: str) -> bool:
    """Return True if a Python module can be imported."""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def pytest_configure(config):
    """Register custom markers so pytest doesn't warn."""
    config.addinivalue_line("markers", "gazu_only: Test requires the gazu backend")
    config.addinivalue_line("markers", "shotgun_only: Test requires the shotgun_api3 backend")


def pytest_collection_modifyitems(config, items):
    """
    Automatically skip tests marked with @pytest.mark.gazu_only or
    @pytest.mark.shotgun_only if the corresponding module is not installed.
    """
    gazu_available = _module_available("gazu")
    shotgun_available = _module_available("shotgun_api3")

    for item in items:
        # Gazu backend
        if "gazu_only" in item.keywords and not gazu_available:
            item.add_marker(
                pytest.mark.skip(reason="Requires gazu backend (`uv run -e gazu`)"),
            )

        # Shotgun backend
        if "shotgun_only" in item.keywords and not shotgun_available:
            item.add_marker(
                pytest.mark.skip(reason="Requires shotgun backend (`uv run -e shotgun`)"),
            )