import pytest

from rez_production_context.connectors.base import EntityNotFoundError
from rez_production_context.connectors.kitsu import Kitsu
from rez_production_context.contexts import Asset, AssetType, Project, Sequence, Shot

# ===========================================================================
# Shared constants
# ===========================================================================

PROJECT_NAME = "Big Buck Bunny"
ASSET_TYPE_NAME = "Character"
ASSET_NAME = "Bunny"
SEQUENCE_NAME = "SQ010"
SHOT_NAME = "SH010"

# ===========================================================================
# Unit tests (no backend required)
# ===========================================================================


@pytest.fixture
def mock_gazu(mocker):
    gazu = mocker.MagicMock()
    mocker.patch.object(Kitsu, "_gazu", return_value=gazu)
    return gazu


@pytest.fixture
def connector(mock_gazu):
    instance = object.__new__(Kitsu)
    instance.server_address = "http://localhost:8080"
    return instance


# ---------------------------------------------------------------------------
# available() and _gazu()
# ---------------------------------------------------------------------------


def test_available_returns_true(mocker):
    mocker.patch("importlib.import_module")
    assert Kitsu.available() is True


def test_available_returns_false_when_import_fails(mocker):
    mocker.patch("importlib.import_module", side_effect=ImportError)
    assert Kitsu.available() is False


def test_gazu_returns_imported_module(mocker):
    mock_module = mocker.MagicMock()
    mocker.patch("importlib.import_module", return_value=mock_module)
    assert Kitsu._gazu() is mock_module


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_init_with_api_key_only(mocker):
    mock_gazu_module = mocker.MagicMock()
    mocker.patch.object(Kitsu, "_gazu", return_value=mock_gazu_module)
    Kitsu(url="http://localhost:8080", api_key="token123")
    mock_gazu_module.set_host.assert_called_once_with("http://localhost:8080")
    mock_gazu_module.set_token.assert_called_once_with("token123")


def test_init_with_email(mocker):
    mock_gazu_module = mocker.MagicMock()
    mocker.patch.object(Kitsu, "_gazu", return_value=mock_gazu_module)
    Kitsu(url="http://localhost:8080", api_key="password", email="user@studio.com")
    mock_gazu_module.log_in.assert_called_once_with("user@studio.com", "password")


# ---------------------------------------------------------------------------
# get_projects / get_project
# ---------------------------------------------------------------------------


def test_get_projects_returns_list(connector, mock_gazu):
    mock_gazu.project.all_projects.return_value = [{"name": PROJECT_NAME}]
    result = connector.get_projects()
    assert isinstance(result, list)
    assert isinstance(result[0], Project)
    assert result[0].name == PROJECT_NAME


def test_get_project_returns_project(connector, mock_gazu):
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    result = connector.get_project(PROJECT_NAME)
    assert isinstance(result, Project)
    assert result.name == PROJECT_NAME


def test_get_project_raises_when_not_found(connector, mock_gazu):
    mock_gazu.project.get_project_by_name.return_value = None
    with pytest.raises(EntityNotFoundError):
        connector.get_project("Does Not Exist")


# ---------------------------------------------------------------------------
# get_asset_types / get_asset_type
# ---------------------------------------------------------------------------


def test_get_asset_types_returns_list(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.asset.all_asset_types_for_project.return_value = [{"name": ASSET_TYPE_NAME}]
    result = connector.get_asset_types(project)
    assert isinstance(result, list)
    assert isinstance(result[0], AssetType)


def test_get_asset_type_returns_asset_type(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.asset.all_asset_types_for_project.return_value = [{"name": ASSET_TYPE_NAME}]
    result = connector.get_asset_type(project, ASSET_TYPE_NAME)
    assert isinstance(result, AssetType)
    assert result.name == ASSET_TYPE_NAME


def test_get_asset_type_raises_when_not_found(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.asset.all_asset_types_for_project.return_value = [{"name": "Other"}]
    with pytest.raises(EntityNotFoundError):
        connector.get_asset_type(project, "DoesNotExist")


# ---------------------------------------------------------------------------
# get_assets / get_asset
# ---------------------------------------------------------------------------


def test_get_assets_returns_list(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    asset_type = AssetType(ASSET_TYPE_NAME, project)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.asset.get_asset_type_by_name.return_value = {"name": ASSET_TYPE_NAME}
    mock_gazu.asset.all_assets_for_project_and_type.return_value = [{"name": ASSET_NAME}]
    result = connector.get_assets(project, asset_type)
    assert isinstance(result, list)
    assert isinstance(result[0], Asset)


def test_get_asset_returns_asset(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    asset_type = AssetType(ASSET_TYPE_NAME, project)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.asset.get_asset_by_name.return_value = {"name": ASSET_NAME}
    result = connector.get_asset(project, asset_type, ASSET_NAME)
    assert isinstance(result, Asset)
    assert result.name == ASSET_NAME


def test_get_asset_raises_when_not_found(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    asset_type = AssetType(ASSET_TYPE_NAME, project)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.asset.get_asset_by_name.return_value = None
    with pytest.raises(EntityNotFoundError):
        connector.get_asset(project, asset_type, "DoesNotExist")


# ---------------------------------------------------------------------------
# get_sequences / get_sequence
# ---------------------------------------------------------------------------


def test_get_sequences_returns_list(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.shot.all_sequences_for_project.return_value = [{"name": SEQUENCE_NAME}]
    result = connector.get_sequences(project)
    assert isinstance(result, list)
    assert isinstance(result[0], Sequence)


def test_get_sequence_returns_sequence(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.shot.get_sequence_by_name.return_value = {"name": SEQUENCE_NAME}
    result = connector.get_sequence(project, SEQUENCE_NAME)
    assert isinstance(result, Sequence)
    assert result.name == SEQUENCE_NAME


def test_get_sequence_raises_when_not_found(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.shot.get_sequence_by_name.return_value = None
    with pytest.raises(EntityNotFoundError):
        connector.get_sequence(project, "DoesNotExist")


# ---------------------------------------------------------------------------
# get_shots / get_shot
# ---------------------------------------------------------------------------


def test_get_shots_returns_list(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.shot.get_sequence_by_name.return_value = {"name": SEQUENCE_NAME}
    mock_gazu.shot.all_shots_for_sequence.return_value = [{"name": SHOT_NAME}]
    result = connector.get_shots(project, sequence)
    assert isinstance(result, list)
    assert isinstance(result[0], Shot)


def test_get_shot_returns_shot(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.shot.get_sequence_by_name.return_value = {"name": SEQUENCE_NAME}
    mock_gazu.shot.get_shot_by_name.return_value = {"name": SHOT_NAME}
    result = connector.get_shot(project, sequence, SHOT_NAME)
    assert isinstance(result, Shot)
    assert result.name == SHOT_NAME


def test_get_shot_raises_when_not_found(connector, mock_gazu):
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    mock_gazu.project.get_project_by_name.return_value = {"name": PROJECT_NAME}
    mock_gazu.shot.get_sequence_by_name.return_value = {"name": SEQUENCE_NAME}
    mock_gazu.shot.get_shot_by_name.return_value = None
    with pytest.raises(EntityNotFoundError):
        connector.get_shot(project, sequence, "DoesNotExist")

