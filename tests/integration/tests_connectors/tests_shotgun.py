import os

import pytest

from rez_production_context.connectors.base import EntityNotFoundError
from rez_production_context.connectors.shotgun import Shotgun
from rez_production_context.contexts import Asset, AssetType, Project, Sequence, Shot

pytestmark = [pytest.mark.integration, pytest.mark.shotgun_only]

# ===========================================================================
# Constants
# ===========================================================================

PROJECT_NAME = "Big Buck Bunny"

BBB_ASSET_TYPES = ["Character", "Prop", "Set", "FX"]

BBB_ASSETS = {
    "Character": ["Bunny", "Frank", "Ringtail"],
    "Prop": ["Tree", "Rock", "Mushroom"],
    "Set": ["Forest", "Cave"],
    "FX": ["Dust", "Water"],
}

BBB_SEQUENCES = ["SQ010", "SQ020", "SQ030"]

BBB_SHOTS = {
    "SQ010": ["SH010", "SH020", "SH030"],
    "SQ020": ["SH010", "SH020"],
    "SQ030": ["SH010"],
}


# ===========================================================================
# Fixtures
# ===========================================================================


@pytest.fixture
def mockgun_sg(tmp_path_factory):
    """A fresh Mockgun instance pre-populated with Big Buck Bunny data."""
    shotgun_api3 = pytest.importorskip(
        "shotgun_api3", reason="This test requires shotgun_api3."
    )
    pytest.importorskip(
        "shotgun_api3.lib.mockgun", reason="This test requires shotgun_api3.lib.mockgun."
    )

    mockgun_temp_path = tmp_path_factory.mktemp("mockgun")

    sg_production = shotgun_api3.Shotgun(
        os.environ.get("SHOTGUN_SERVER_URL"),
        script_name=os.environ.get("SHOTGUN_SCRIPT_NAME"),
        api_key=os.environ.get("SHOTGUN_API_KEY"),
    )
    shotgun_api3.lib.mockgun.generate_schema(
        sg_production,
        mockgun_temp_path / "schema",
        mockgun_temp_path / "entity_schema",
    )

    shotgun_api3.lib.mockgun.Shotgun.set_schema_paths(
        mockgun_temp_path / "schema", mockgun_temp_path / "entity_schema"
    )
    sg = shotgun_api3.lib.mockgun.Shotgun(
        os.environ.get("SHOTGUN_SERVER_URL"),
        script_name=os.environ.get("SHOTGUN_SCRIPT_NAME"),
        api_key=os.environ.get("SHOTGUN_API_KEY"),
    )

    project = sg.create("Project", {"code": PROJECT_NAME})

    for asset_type_name in BBB_ASSET_TYPES:
        for asset_name in BBB_ASSETS[asset_type_name]:
            sg.create(
                "Asset",
                {
                    "code": asset_name,
                    "sg_asset_type": asset_type_name,
                    "project": {"type": "Project", "id": project["id"]},
                },
            )

    for seq_name in BBB_SEQUENCES:
        sequence = sg.create(
            "Sequence",
            {
                "code": seq_name,
                "project": {"type": "Project", "id": project["id"]},
            },
        )
        for shot_name in BBB_SHOTS[seq_name]:
            sg.create(
                "Shot",
                {
                    "code": shot_name,
                    "project": {"type": "Project", "id": project["id"]},
                    "sg_sequence": {"type": "Sequence", "id": sequence["id"]},
                },
            )

    return sg


@pytest.fixture
def sg_connector(mockgun_sg):
    """A Shotgun connector backed by the Mockgun instance."""
    instance = object.__new__(Shotgun)
    instance.server_address = "https://studio.shotgunstudio.com"
    instance._sg_instance = mockgun_sg
    return instance


# ===========================================================================
# Tests
# ===========================================================================


def test_available_returns_true():
    assert Shotgun.available() is True


def test_init_creates_sg_connection(mocker):
    mock_sg_cls = mocker.patch("shotgun_api3.Shotgun")
    instance = Shotgun(
        url="https://test.shotgunstudio.com",
        script_name="test_script",
        api_key="test_key",
    )
    mock_sg_cls.assert_called_once_with(
        "https://test.shotgunstudio.com",
        script_name="test_script",
        api_key="test_key",
    )
    assert instance.server_address == "https://test.shotgunstudio.com"


def test_get_projects_returns_list(sg_connector):
    assert isinstance(sg_connector.get_projects(), list)


def test_get_projects_contains_bbb(sg_connector):
    names = [p.name for p in sg_connector.get_projects()]
    assert PROJECT_NAME in names


def test_get_projects_returns_project_instances(sg_connector):
    assert all(isinstance(p, Project) for p in sg_connector.get_projects())


def test_get_project_returns_project_instance(sg_connector):
    assert isinstance(sg_connector.get_project(PROJECT_NAME), Project)


def test_get_project_correct_name(sg_connector):
    assert sg_connector.get_project(PROJECT_NAME).name == PROJECT_NAME


def test_get_project_raises_when_not_found(sg_connector):
    with pytest.raises(EntityNotFoundError):
        sg_connector.get_project("Does Not Exist")


def test_get_asset_types_returns_list(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert isinstance(sg_connector.get_asset_types(project), list)


def test_get_asset_types_contains_all(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    names = [at.name for at in sg_connector.get_asset_types(project)]
    assert all(expected in names for expected in BBB_ASSET_TYPES)


def test_get_asset_types_returns_asset_type_instances(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert all(isinstance(at, AssetType) for at in sg_connector.get_asset_types(project))


def test_get_asset_type_returns_asset_type_instance(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert isinstance(sg_connector.get_asset_type(project, "Character"), AssetType)


def test_get_asset_type_correct_name(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert sg_connector.get_asset_type(project, "Character").name == "Character"


def test_get_asset_types_raises_when_project_not_found(sg_connector):
    with pytest.raises(EntityNotFoundError):
        sg_connector.get_asset_types(Project("Does Not Exist"))


def test_get_assets_returns_list(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    asset_type = sg_connector.get_asset_type(project, "Character")
    assert isinstance(sg_connector.get_assets(project, asset_type), list)


def test_get_assets_contains_all(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    asset_type = sg_connector.get_asset_type(project, "Character")
    names = [a.name for a in sg_connector.get_assets(project, asset_type)]
    assert all(expected in names for expected in BBB_ASSETS["Character"])


def test_get_assets_returns_asset_instances(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    asset_type = sg_connector.get_asset_type(project, "Character")
    assert all(isinstance(a, Asset) for a in sg_connector.get_assets(project, asset_type))


def test_get_asset_returns_asset_instance(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    asset_type = sg_connector.get_asset_type(project, "Character")
    assert isinstance(sg_connector.get_asset(project, asset_type, "Bunny"), Asset)


def test_get_asset_correct_name(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    asset_type = sg_connector.get_asset_type(project, "Character")
    assert sg_connector.get_asset(project, asset_type, "Bunny").name == "Bunny"


def test_get_asset_raises_when_not_found(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    asset_type = sg_connector.get_asset_type(project, "Character")
    with pytest.raises(EntityNotFoundError):
        sg_connector.get_asset(project, asset_type, "Does Not Exist")


def test_get_sequences_returns_list(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert isinstance(sg_connector.get_sequences(project), list)


def test_get_sequences_contains_all(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    names = [s.name for s in sg_connector.get_sequences(project)]
    assert all(expected in names for expected in BBB_SEQUENCES)


def test_get_sequences_returns_sequence_instances(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert all(isinstance(s, Sequence) for s in sg_connector.get_sequences(project))


def test_get_sequence_returns_sequence_instance(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert isinstance(sg_connector.get_sequence(project, "SQ010"), Sequence)


def test_get_sequence_correct_name(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    assert sg_connector.get_sequence(project, "SQ010").name == "SQ010"


def test_get_sequence_raises_when_not_found(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    with pytest.raises(EntityNotFoundError):
        sg_connector.get_sequence(project, "SQ999")


def test_get_shots_returns_list(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    sequence = sg_connector.get_sequence(project, "SQ010")
    assert isinstance(sg_connector.get_shots(project, sequence), list)


def test_get_shots_contains_all(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    sequence = sg_connector.get_sequence(project, "SQ010")
    names = [s.name for s in sg_connector.get_shots(project, sequence)]
    assert all(expected in names for expected in BBB_SHOTS["SQ010"])


def test_get_shots_returns_shot_instances(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    sequence = sg_connector.get_sequence(project, "SQ010")
    assert all(isinstance(s, Shot) for s in sg_connector.get_shots(project, sequence))


def test_get_shot_returns_shot_instance(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    sequence = sg_connector.get_sequence(project, "SQ010")
    assert isinstance(sg_connector.get_shot(project, sequence, "SH010"), Shot)


def test_get_shot_correct_name(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    sequence = sg_connector.get_sequence(project, "SQ010")
    assert sg_connector.get_shot(project, sequence, "SH010").name == "SH010"


def test_get_shots_raises_when_sequence_not_found(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    with pytest.raises(EntityNotFoundError):
        sg_connector.get_shots(project, Sequence("SQ999", project))


def test_get_shot_raises_when_not_found(sg_connector):
    project = sg_connector.get_project(PROJECT_NAME)
    sequence = sg_connector.get_sequence(project, "SQ010")
    with pytest.raises(EntityNotFoundError):
        sg_connector.get_shot(project, sequence, "SH999")