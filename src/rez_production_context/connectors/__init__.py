import importlib

from .base import Base

_CONNECTOR_REGISTRY: list[tuple[str, str]] = [
    (".kitsu", "Kitsu"),
    (".shotgun", "Shotgun"),
]


def _load_connectors() -> list[type[Base]]:
    """Load and return all available connector classes from the registry."""
    connectors: list[type[Base]] = []
    for mod, cls_name in _CONNECTOR_REGISTRY:
        try:
            module = importlib.import_module(mod, package=__name__)
            cls = getattr(module, cls_name)
            if cls.available():
                connectors.append(cls)
        except Exception:
            pass
    return connectors


CONNECTORS: list[type[Base]] = _load_connectors()