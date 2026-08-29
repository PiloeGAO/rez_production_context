import configparser
from threading import Lock

import pytest

from rez_production_context.constants import CONFIG_FILE_ENV
from rez_production_context.contexts import Asset, AssetType, Project, Sequence, Shot
from rez_production_context.manager import Manager, SingletonMeta

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FakeConnector:
    @classmethod
    def name(cls):
        return "Fake"

    @staticmethod
    def available():
        return True

    def __init__(self, **kwargs):
        pass


def _write_config(tmp_path, sections: dict, cache: bool = False) -> str:
    parser = configparser.ConfigParser()
    parser["DEFAULT"]["cache"] = "yes" if cache else "no"
    for section, options in sections.items():
        parser[section] = options
    path = tmp_path / "config.ini"
    with open(path, "w") as f:
        parser.write(f)
    return str(path)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton():
    SingletonMeta._instances.pop(Manager, None)
    yield
    SingletonMeta._instances.pop(Manager, None)


@pytest.fixture
def manager(mocker):
    """Manager with a mock connector, bypassing __init__ and the singleton."""
    instance = object.__new__(Manager)
    instance.connector = mocker.MagicMock()
    instance._cache = {}
    instance._cache_lock = Lock()
    instance._cache_enabled = False
    return instance


# ---------------------------------------------------------------------------
# _read_config — FileNotFoundError
# ---------------------------------------------------------------------------


def test_read_config_raises_when_env_var_unset(monkeypatch):
    monkeypatch.delenv(CONFIG_FILE_ENV, raising=False)
    with pytest.raises(FileNotFoundError):
        Manager()


def test_read_config_raises_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.setenv(CONFIG_FILE_ENV, str(tmp_path / "missing.ini"))
    with pytest.raises(FileNotFoundError):
        Manager()


# ---------------------------------------------------------------------------
# _read_config — RuntimeError
# ---------------------------------------------------------------------------


def test_read_config_raises_when_no_connector(monkeypatch, tmp_path):
    path = _write_config(tmp_path, {"OTHER": {}})
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeConnector])
    with pytest.raises(RuntimeError, match="at least one connector"):
        Manager()


def test_read_config_raises_when_multiple_connectors(monkeypatch, tmp_path):
    class _FakeA:
        @classmethod
        def name(cls):
            return "FakeA"

        @staticmethod
        def available():
            return True

        def __init__(self, **kwargs):
            pass

    class _FakeB:
        @classmethod
        def name(cls):
            return "FakeB"

        @staticmethod
        def available():
            return True

        def __init__(self, **kwargs):
            pass

    path = _write_config(tmp_path, {"FAKEA": {}, "FAKEB": {}})
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeA, _FakeB])
    with pytest.raises(RuntimeError, match="Only one connector"):
        Manager()


# ---------------------------------------------------------------------------
# _read_config — valid config
# ---------------------------------------------------------------------------


def test_read_config_initializes_connector(monkeypatch, tmp_path):
    path = _write_config(tmp_path, {"FAKE": {"url": "http://localhost"}})
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeConnector])
    mgr = Manager()
    assert isinstance(mgr.connector, _FakeConnector)


def test_read_config_cache_enabled_when_set_in_config(monkeypatch, tmp_path):
    path = _write_config(tmp_path, {"FAKE": {}}, cache=True)
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeConnector])
    assert Manager().cache is True


def test_read_config_cache_disabled_when_set_in_config(monkeypatch, tmp_path):
    path = _write_config(tmp_path, {"FAKE": {}}, cache=False)
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeConnector])
    assert Manager().cache is False


def test_manager_is_singleton(monkeypatch, tmp_path):
    path = _write_config(tmp_path, {"FAKE": {}})
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeConnector])
    assert Manager() is Manager()


def test_manager_init_is_noop_when_already_initialized(monkeypatch, tmp_path):
    path = _write_config(tmp_path, {"FAKE": {}})
    monkeypatch.setenv(CONFIG_FILE_ENV, path)
    monkeypatch.setattr("rez_production_context.manager.CONNECTORS", [_FakeConnector])
    mgr = Manager()
    original_connector = mgr.connector
    mgr.__init__()
    assert mgr.connector is original_connector


# ---------------------------------------------------------------------------
# _active_connector
# ---------------------------------------------------------------------------


def test_active_connector_raises_when_not_initialized(manager):
    manager.connector = None
    with pytest.raises(RuntimeError, match="No connector initialised"):
        _ = manager._active_connector


# ---------------------------------------------------------------------------
# cache property
# ---------------------------------------------------------------------------


def test_cache_default_is_false(manager):
    assert manager.cache is False


def test_cache_can_be_enabled(manager):
    manager.cache = True
    assert manager.cache is True


def test_cache_setter_clears_stored_entries_when_disabled(manager):
    manager._cache = {"some:key": "value"}
    manager._cache_enabled = True
    manager.cache = False
    assert manager._cache == {}


def test_cache_setter_preserves_entries_when_enabled(manager):
    manager._cache = {"some:key": "value"}
    manager.cache = True
    assert "some:key" in manager._cache


# ---------------------------------------------------------------------------
# _cached decorator
# ---------------------------------------------------------------------------


def test_cached_calls_connector_on_cache_miss(manager):
    expected = [Project("BBB")]
    manager.connector.get_projects.return_value = expected
    assert manager.get_projects() is expected


def test_cached_returns_same_object_on_cache_hit(manager):
    manager.cache = True
    expected = [Project("BBB")]
    manager.connector.get_projects.return_value = expected
    first = manager.get_projects()
    second = manager.get_projects()
    assert first is second
    manager.connector.get_projects.assert_called_once()


def test_cached_calls_connector_every_time_when_cache_disabled(manager):
    manager.cache = False
    manager.connector.get_projects.return_value = []
    manager.get_projects()
    manager.get_projects()
    assert manager.connector.get_projects.call_count == 2


def test_cached_uses_entity_name_as_key(manager):
    manager.cache = True
    project = Project("BBB")
    manager.connector.get_asset_types.side_effect = lambda p: [AssetType(p.name + "_type", p)]
    manager.get_asset_types(project)
    manager.get_asset_types(project)
    manager.connector.get_asset_types.assert_called_once()


def test_cached_uses_separate_key_per_argument(manager):
    manager.cache = True
    manager.connector.get_project.side_effect = lambda name: Project(name)
    manager.get_project("BBB")
    manager.get_project("Elephants Dream")
    assert manager.connector.get_project.call_count == 2


def test_cached_reuses_key_for_same_argument(manager):
    manager.cache = True
    manager.connector.get_project.return_value = Project("BBB")
    manager.get_project("BBB")
    manager.get_project("BBB")
    manager.connector.get_project.assert_called_once()


# ---------------------------------------------------------------------------
# get_* methods — delegation to connector
# ---------------------------------------------------------------------------


def test_get_projects_delegates_to_connector(manager):
    expected = [Project("BBB")]
    manager.connector.get_projects.return_value = expected
    assert manager.get_projects() is expected


def test_get_project_delegates_to_connector(manager):
    expected = Project("BBB")
    manager.connector.get_project.return_value = expected
    assert manager.get_project("BBB") is expected
    manager.connector.get_project.assert_called_once_with("BBB")


def test_get_asset_types_delegates_to_connector(manager):
    project = Project("BBB")
    expected = [AssetType("Character", project)]
    manager.connector.get_asset_types.return_value = expected
    assert manager.get_asset_types(project) is expected
    manager.connector.get_asset_types.assert_called_once_with(project)


def test_get_asset_type_delegates_to_connector(manager):
    project = Project("BBB")
    expected = AssetType("Character", project)
    manager.connector.get_asset_type.return_value = expected
    assert manager.get_asset_type(project, "Character") is expected
    manager.connector.get_asset_type.assert_called_once_with(project, "Character")


def test_get_assets_delegates_to_connector(manager):
    project = Project("BBB")
    asset_type = AssetType("Character", project)
    expected = [Asset("Bunny", asset_type)]
    manager.connector.get_assets.return_value = expected
    assert manager.get_assets(project, asset_type) is expected
    manager.connector.get_assets.assert_called_once_with(project, asset_type)


def test_get_asset_delegates_to_connector(manager):
    project = Project("BBB")
    asset_type = AssetType("Character", project)
    expected = Asset("Bunny", asset_type)
    manager.connector.get_asset.return_value = expected
    assert manager.get_asset(project, asset_type, "Bunny") is expected
    manager.connector.get_asset.assert_called_once_with(project, asset_type, "Bunny")


def test_get_sequences_delegates_to_connector(manager):
    project = Project("BBB")
    expected = [Sequence("SQ010", project)]
    manager.connector.get_sequences.return_value = expected
    assert manager.get_sequences(project) is expected
    manager.connector.get_sequences.assert_called_once_with(project)


def test_get_sequence_delegates_to_connector(manager):
    project = Project("BBB")
    expected = Sequence("SQ010", project)
    manager.connector.get_sequence.return_value = expected
    assert manager.get_sequence(project, "SQ010") is expected
    manager.connector.get_sequence.assert_called_once_with(project, "SQ010")


def test_get_shots_delegates_to_connector(manager):
    project = Project("BBB")
    sequence = Sequence("SQ010", project)
    expected = [Shot("SH010", sequence)]
    manager.connector.get_shots.return_value = expected
    assert manager.get_shots(project, sequence) is expected
    manager.connector.get_shots.assert_called_once_with(project, sequence)


def test_get_shot_delegates_to_connector(manager):
    project = Project("BBB")
    sequence = Sequence("SQ010", project)
    expected = Shot("SH010", sequence)
    manager.connector.get_shot.return_value = expected
    assert manager.get_shot(project, sequence, "SH010") is expected
    manager.connector.get_shot.assert_called_once_with(project, sequence, "SH010")
