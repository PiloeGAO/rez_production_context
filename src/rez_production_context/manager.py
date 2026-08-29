"""Context manager used to perform calls to the api."""

import configparser
import functools
import os
from threading import Lock

from .connectors import CONNECTORS, Base
from .constants import CONFIG_FILE_ENV, STUDIO_CONTEXT_ENV
from .contexts import Asset, AssetType, Project, Sequence, Shot, Studio


def _cached(method):
    """Decorator that caches the return value of a Manager method.

    The cache key is built from the method name and its arguments, using
    ``.name`` for entity objects and ``str()`` for plain values. Caching
    is skipped entirely when ``Manager.cache`` is ``False``.
    """

    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        key = (
            method.__name__
            + ":"
            + ":".join(arg.name if hasattr(arg, "name") else str(arg) for arg in args)
        )
        with self._cache_lock:
            if self.cache and key in self._cache:
                return self._cache[key]
        result = method(self, *args, **kwargs)
        with self._cache_lock:
            if self.cache:
                self._cache[key] = result
        return result

    return wrapper


class SingletonMeta(type):
    """This is a thread-safe implementation of Singleton.

    Source: https://refactoring.guru/design-patterns/singleton/python/example
    """

    _instances: dict[type, object] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        """Custom call function for a threadsafe singleton."""
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class Manager(metaclass=SingletonMeta):
    """Central singleton that initialises the active connector and routes all
    production-data requests through it.

    Configuration is read from the INI file pointed to by the
    ``RESOLVER_CONTEXT_CONFIG`` environment variable.  When ``cache = yes`` is
    set in the ``[DEFAULT]`` section, results are stored in memory and reused
    for the lifetime of the process.
    """

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._initialized = True

        self.connector: "Base | None" = None
        self._cache: dict = {}
        self._cache_lock: Lock = Lock()
        self._cache_enabled = False

        self._read_config()

        self.studio = Studio(name=os.environ.get(STUDIO_CONTEXT_ENV, "studio"))

    @property
    def cache(self) -> bool:
        """Whether result caching is currently enabled."""
        return self._cache_enabled

    @cache.setter
    def cache(self, value: bool) -> None:
        """Enable or disable caching. Disabling also clears all stored results."""
        self._cache_enabled = value
        if not value:
            self._cache.clear()

    @property
    def _active_connector(self) -> "Base":
        """Return the active connector, raising if not yet initialised."""
        if self.connector is None:
            raise RuntimeError("No connector initialised. Call _read_config() first.")
        return self.connector

    def _read_config(self) -> None:
        """Read the config file from disk and initialize the connector."""
        if not os.path.isfile(os.environ.get(CONFIG_FILE_ENV, "")):
            raise FileNotFoundError(
                'No config file found in the "{}" environment variable.'.format(
                    CONFIG_FILE_ENV
                )
            )

        parser = configparser.ConfigParser()
        parser.read(os.environ[CONFIG_FILE_ENV])

        connectors = [
            connector
            for connector in CONNECTORS
            if connector.name().upper() in parser.sections()
        ]
        if not connectors:
            raise RuntimeError(
                "Please use at least one connector in the config: {}".format(
                    ", ".join([connector.name().upper() for connector in CONNECTORS])
                )
            )
        if len(connectors) > 1:
            raise RuntimeError(
                "Only one connector can be used at a time, found: {}".format(
                    ", ".join([connector.name().upper() for connector in connectors])
                )
            )
        connector = connectors[0]
        connector_config_key = connector.name().upper()

        options = {
            name: parser[connector_config_key][name]
            for name in parser[connector_config_key]
        }

        self.connector = connector(**options)

        self.cache = parser.getboolean("DEFAULT", "cache", fallback=False)

    @_cached
    def get_projects(self) -> list[Project]:
        """Return all projects available in the production database."""
        return self._active_connector.get_projects()

    @_cached
    def get_project(self, project_name: str) -> Project:
        """Return the project matching ``project_name``.

        Args:
            project_name: Name of the project to retrieve.
        """
        return self._active_connector.get_project(project_name)

    @_cached
    def get_asset_types(self, project: Project) -> list[AssetType]:
        """Return all asset types defined in ``project``.

        Args:
            project: The project to query.
        """
        return self._active_connector.get_asset_types(project)

    @_cached
    def get_asset_type(self, project: Project, asset_type_name: str) -> AssetType:
        """Return the asset type matching ``asset_type_name`` within ``project``.

        Args:
            project: The project to query.
            asset_type_name: Name of the asset type to retrieve.
        """
        return self._active_connector.get_asset_type(project, asset_type_name)

    @_cached
    def get_assets(self, project: Project, asset_type: AssetType) -> list[Asset]:
        """Return all assets of ``asset_type`` within ``project``.

        Args:
            project: The project to query.
            asset_type: The asset type to filter by.
        """
        return self._active_connector.get_assets(project, asset_type)

    @_cached
    def get_asset(
        self, project: Project, asset_type: AssetType, asset_name: str
    ) -> Asset:
        """Return the asset matching ``asset_name`` within ``project`` and ``asset_type``.

        Args:
            project: The project to query.
            asset_type: The asset type to filter by.
            asset_name: Name of the asset to retrieve.
        """
        return self._active_connector.get_asset(project, asset_type, asset_name)

    @_cached
    def get_sequences(self, project: Project) -> list[Sequence]:
        """Return all sequences within ``project``.

        Args:
            project: The project to query.
        """
        return self._active_connector.get_sequences(project)

    @_cached
    def get_sequence(self, project: Project, sequence_name: str) -> Sequence:
        """Return the sequence matching ``sequence_name`` within ``project``.

        Args:
            project: The project to query.
            sequence_name: Name of the sequence to retrieve.
        """
        return self._active_connector.get_sequence(project, sequence_name)

    @_cached
    def get_shots(self, project: Project, sequence: Sequence) -> list[Shot]:
        """Return all shots within ``sequence``.

        Args:
            project: The project containing the sequence.
            sequence: The sequence to query.
        """
        return self._active_connector.get_shots(project, sequence)

    @_cached
    def get_shot(self, project: Project, sequence: Sequence, shot_name: str) -> Shot:
        """Return the shot matching ``shot_name`` within ``sequence``.

        Args:
            project: The project containing the sequence.
            sequence: The sequence containing the shot.
            shot_name: Name of the shot to retrieve.
        """
        return self._active_connector.get_shot(project, sequence, shot_name)
