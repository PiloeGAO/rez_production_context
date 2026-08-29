import pytest

from rez_production_context.connectors.base import Base


class _MinimalConnector(Base):
    """Concrete subclass that delegates every method to super() to exercise Base bodies."""

    @staticmethod
    def available() -> bool:
        return False

    def get_project(self, project_name):
        return super().get_project(project_name)

    def get_projects(self):
        return super().get_projects()

    def get_asset_type(self, project, asset_type_name):
        return super().get_asset_type(project, asset_type_name)

    def get_asset_types(self, project):
        return super().get_asset_types(project)

    def get_asset(self, project, asset_type, asset_name):
        return super().get_asset(project, asset_type, asset_name)

    def get_assets(self, project, asset_type):
        return super().get_assets(project, asset_type)

    def get_sequence(self, project, sequence_name):
        return super().get_sequence(project, sequence_name)

    def get_sequences(self, project):
        return super().get_sequences(project)

    def get_shot(self, project, sequence, shot_name):
        return super().get_shot(project, sequence, shot_name)

    def get_shots(self, project, sequence):
        return super().get_shots(project, sequence)


@pytest.fixture
def connector():
    return _MinimalConnector()


# ---------------------------------------------------------------------------
# Base.__init__ and name()
# ---------------------------------------------------------------------------


def test_base_init_accepts_kwargs():
    assert _MinimalConnector(unused="value") is not None


def test_base_name_returns_class_name():
    assert _MinimalConnector.name() == "_MinimalConnector"


# ---------------------------------------------------------------------------
# Abstract method bodies all raise NotImplementedError
# ---------------------------------------------------------------------------


def test_available_abstract_body_raises():
    with pytest.raises(NotImplementedError):
        Base.available()


def test_get_project_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_project("BBB")


def test_get_projects_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_projects()


def test_get_asset_type_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_asset_type(None, "Character")


def test_get_asset_types_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_asset_types(None)


def test_get_asset_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_asset(None, None, "Bunny")


def test_get_assets_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_assets(None, None)


def test_get_sequence_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_sequence(None, "SQ010")


def test_get_sequences_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_sequences(None)


def test_get_shot_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_shot(None, None, "SH010")


def test_get_shots_raises(connector):
    with pytest.raises(NotImplementedError):
        connector.get_shots(None, None)