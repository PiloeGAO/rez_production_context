import os

import pytest

from rez_production_context.connectors.base import EntityNotFoundError
from rez_production_context.connectors.shotgun import Shotgun
from rez_production_context.contexts import Asset, AssetType, Project, Sequence, Shot

# ===========================================================================
# Shared constants
# ===========================================================================

PROJECT_NAME = "Big Buck Bunny"
ASSET_TYPE_NAME = "Character"
ASSET_NAME = "Bunny"
SEQUENCE_NAME = "SQ010"
SHOT_NAME = "SH010"

PROJECT_ID = 1
SEQUENCE_ID = 10

# ===========================================================================
# Unit tests (no backend required)
# ===========================================================================


@pytest.fixture
def mock_sg(mocker):
    return mocker.MagicMock()


@pytest.fixture
def connector(mock_sg):
    instance = object.__new__(Shotgun)
    instance._sg_instance = mock_sg
    return instance


# ---------------------------------------------------------------------------
# available() and _sg()
# ---------------------------------------------------------------------------


def test_available_returns_true(mocker):
    mocker.patch("importlib.import_module")
    assert Shotgun.available() is True


def test_available_returns_false_when_import_fails(mocker):
    mocker.patch("importlib.import_module", side_effect=ImportError)
    assert Shotgun.available() is False


def test_sg_returns_imported_module(mocker):
    mock_module = mocker.MagicMock()
    mocker.patch("importlib.import_module", return_value=mock_module)
    assert Shotgun._sg() is mock_module


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_init_creates_shotgun_instance(mocker):
    mock_sg_module = mocker.MagicMock()
    mocker.patch.object(Shotgun, "_sg", return_value=mock_sg_module)
    Shotgun(url="https://studio.shotgunstudio.com", script_name="my_script", api_key="abc123")
    mock_sg_module.Shotgun.assert_called_once_with(
        "https://studio.shotgunstudio.com",
        script_name="my_script",
        api_key="abc123",
    )


# ---------------------------------------------------------------------------
# _find_sg_project
# ---------------------------------------------------------------------------


def test_find_sg_project_raises_when_not_found(connector, mock_sg):
    mock_sg.find_one.return_value = None
    project = Project(PROJECT_NAME)
    with pytest.raises(EntityNotFoundError):
        connector._find_sg_project(project)


def test_find_sg_project_returns_dict(connector, mock_sg):
    mock_sg.find_one.return_value = {"id": PROJECT_ID}
    project = Project(PROJECT_NAME)
    result = connector._find_sg_project(project)
    assert result == {"id": PROJECT_ID}


# ---------------------------------------------------------------------------
# _find_sg_sequence
# ---------------------------------------------------------------------------


def test_find_sg_sequence_raises_when_not_found(connector, mock_sg):
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, None]
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    with pytest.raises(EntityNotFoundError):
        connector._find_sg_sequence(project, sequence)


def test_find_sg_sequence_returns_dict(connector, mock_sg):
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, {"id": SEQUENCE_ID}]
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    result = connector._find_sg_sequence(project, sequence)
    assert result == {"id": SEQUENCE_ID}


# ---------------------------------------------------------------------------
# get_projects / get_project
# ---------------------------------------------------------------------------


def test_get_projects_returns_list(connector, mock_sg):
    mock_sg.find.return_value = [{"code": PROJECT_NAME}]
    result = connector.get_projects()
    assert isinstance(result, list)
    assert isinstance(result[0], Project)
    assert result[0].name == PROJECT_NAME


def test_get_project_returns_project(connector, mock_sg):
    mock_sg.find_one.return_value = {"code": PROJECT_NAME}
    result = connector.get_project(PROJECT_NAME)
    assert isinstance(result, Project)
    assert result.name == PROJECT_NAME


def test_get_project_raises_when_not_found(connector, mock_sg):
    mock_sg.find_one.return_value = None
    with pytest.raises(EntityNotFoundError):
        connector.get_project("Does Not Exist")


# ---------------------------------------------------------------------------
# get_asset_types / get_asset_type
# ---------------------------------------------------------------------------


def test_get_asset_types_returns_list(connector, mock_sg):
    project = Project(PROJECT_NAME)
    mock_sg.find_one.return_value = {"id": PROJECT_ID}
    mock_sg.find.return_value = [
        {"sg_asset_type": ASSET_TYPE_NAME},
        {"sg_asset_type": ASSET_TYPE_NAME},  # duplicate, should be deduplicated
        {"sg_asset_type": "Prop"},
    ]
    result = connector.get_asset_types(project)
    assert isinstance(result, list)
    assert len(result) == 2
    assert all(isinstance(at, AssetType) for at in result)
    assert result[0].name == ASSET_TYPE_NAME


def test_get_asset_types_skips_none_asset_type(connector, mock_sg):
    project = Project(PROJECT_NAME)
    mock_sg.find_one.return_value = {"id": PROJECT_ID}
    mock_sg.find.return_value = [{"sg_asset_type": None}, {"sg_asset_type": ASSET_TYPE_NAME}]
    result = connector.get_asset_types(project)
    assert len(result) == 1
    assert result[0].name == ASSET_TYPE_NAME


def test_get_asset_type_returns_asset_type(connector, mock_sg):
    project = Project(PROJECT_NAME)
    result = connector.get_asset_type(project, ASSET_TYPE_NAME)
    assert isinstance(result, AssetType)
    assert result.name == ASSET_TYPE_NAME


# ---------------------------------------------------------------------------
# get_assets / get_asset
# ---------------------------------------------------------------------------


def test_get_assets_returns_list(connector, mock_sg):
    project = Project(PROJECT_NAME)
    asset_type = AssetType(ASSET_TYPE_NAME, project)
    mock_sg.find_one.return_value = {"id": PROJECT_ID}
    mock_sg.find.return_value = [{"code": ASSET_NAME}]
    result = connector.get_assets(project, asset_type)
    assert isinstance(result, list)
    assert isinstance(result[0], Asset)
    assert result[0].name == ASSET_NAME


def test_get_asset_returns_asset(connector, mock_sg):
    project = Project(PROJECT_NAME)
    asset_type = AssetType(ASSET_TYPE_NAME, project)
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, {"code": ASSET_NAME}]
    result = connector.get_asset(project, asset_type, ASSET_NAME)
    assert isinstance(result, Asset)
    assert result.name == ASSET_NAME


def test_get_asset_raises_when_not_found(connector, mock_sg):
    project = Project(PROJECT_NAME)
    asset_type = AssetType(ASSET_TYPE_NAME, project)
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, None]
    with pytest.raises(EntityNotFoundError):
        connector.get_asset(project, asset_type, "DoesNotExist")


# ---------------------------------------------------------------------------
# get_sequences / get_sequence
# ---------------------------------------------------------------------------


def test_get_sequences_returns_list(connector, mock_sg):
    project = Project(PROJECT_NAME)
    mock_sg.find_one.return_value = {"id": PROJECT_ID}
    mock_sg.find.return_value = [{"code": SEQUENCE_NAME}]
    result = connector.get_sequences(project)
    assert isinstance(result, list)
    assert isinstance(result[0], Sequence)
    assert result[0].name == SEQUENCE_NAME


def test_get_sequence_returns_sequence(connector, mock_sg):
    project = Project(PROJECT_NAME)
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, {"code": SEQUENCE_NAME}]
    result = connector.get_sequence(project, SEQUENCE_NAME)
    assert isinstance(result, Sequence)
    assert result.name == SEQUENCE_NAME


def test_get_sequence_raises_when_not_found(connector, mock_sg):
    project = Project(PROJECT_NAME)
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, None]
    with pytest.raises(EntityNotFoundError):
        connector.get_sequence(project, "DoesNotExist")


# ---------------------------------------------------------------------------
# get_shots / get_shot
# ---------------------------------------------------------------------------


def test_get_shots_returns_list(connector, mock_sg):
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    # get_shots calls _find_sg_project (1 find_one), then _find_sg_sequence
    # which internally calls _find_sg_project again (1 find_one) + sequence find_one
    mock_sg.find_one.side_effect = [{"id": PROJECT_ID}, {"id": PROJECT_ID}, {"id": SEQUENCE_ID}]
    mock_sg.find.return_value = [{"code": SHOT_NAME}]
    result = connector.get_shots(project, sequence)
    assert isinstance(result, list)
    assert isinstance(result[0], Shot)
    assert result[0].name == SHOT_NAME


def test_get_shot_returns_shot(connector, mock_sg):
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    # get_shot: _find_sg_project (1), _find_sg_sequence -> _find_sg_project (1) + sequence (1), then shot (1)
    mock_sg.find_one.side_effect = [
        {"id": PROJECT_ID},
        {"id": PROJECT_ID},
        {"id": SEQUENCE_ID},
        {"code": SHOT_NAME},
    ]
    result = connector.get_shot(project, sequence, SHOT_NAME)
    assert isinstance(result, Shot)
    assert result.name == SHOT_NAME


def test_get_shot_raises_when_not_found(connector, mock_sg):
    project = Project(PROJECT_NAME)
    sequence = Sequence(SEQUENCE_NAME, project)
    mock_sg.find_one.side_effect = [
        {"id": PROJECT_ID},
        {"id": PROJECT_ID},
        {"id": SEQUENCE_ID},
        None,
    ]
    with pytest.raises(EntityNotFoundError):
        connector.get_shot(project, sequence, "DoesNotExist")

