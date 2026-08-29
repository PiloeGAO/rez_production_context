import os

import pytest

from rez_production_context.connectors.kitsu import Kitsu
from rez_production_context.contexts import Asset, AssetType, Project, Sequence, Shot

pytestmark = [pytest.mark.integration, pytest.mark.gazu_only]

# ===========================================================================
# Constants
# ===========================================================================

PROJECT_NAME = "Big Buck Bunny"

ZOU_URL = "http://localhost"
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "mysecretpassword"

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


def _zou_is_responsive() -> bool:
    try:
        import requests

        return requests.get(f"{ZOU_URL}/api/").status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return os.path.join(str(pytestconfig.rootdir), "tests", "integration", "docker-compose.yml")


@pytest.fixture(scope="session")
def zou_service(docker_services, docker_compose_file):
    """Start the Zou service and wait until it is responsive."""
    docker_services.wait_until_responsive(
        timeout=120.0,
        pause=1.0,
        check=_zou_is_responsive,
    )
    return ZOU_URL


@pytest.fixture
def bbb_project(zou_service):
    """Create the Big Buck Bunny project and all its data before each test,
    then delete everything after."""
    gazu = pytest.importorskip("gazu", reason="This test requires gazu.")
    gazu.set_host(f"{zou_service}/api")
    gazu.log_in(ADMIN_EMAIL, ADMIN_PASSWORD)

    jwt_token = ADMIN_PASSWORD

    project = gazu.project.new_project(PROJECT_NAME)

    for asset_type_name in BBB_ASSET_TYPES:
        asset_type = gazu.asset.new_asset_type(asset_type_name)
        for asset_name in BBB_ASSETS.get(asset_type_name, []):
            gazu.asset.new_asset(project, asset_type, asset_name, "")

    for seq_name in BBB_SEQUENCES:
        sequence = gazu.shot.new_sequence(project, seq_name)
        for shot_name in BBB_SHOTS.get(seq_name, []):
            gazu.shot.new_shot(project, sequence, shot_name)

    gazu.log_out()

    yield project, jwt_token


@pytest.fixture
def kitsu_connector(zou_service, bbb_project):
    pytest.importorskip("gazu", reason="This test requires gazu.")
    _, jwt_token = bbb_project
    return Kitsu(f"{zou_service}/api", email=ADMIN_EMAIL, api_key=jwt_token)


# ===========================================================================
# Tests
# ===========================================================================


def test_available_returns_true():
    assert Kitsu.available() is True


def test_get_projects_returns_list(kitsu_connector):
    assert isinstance(kitsu_connector.get_projects(), list)


def test_get_projects_contains_bbb(kitsu_connector):
    names = [p.name for p in kitsu_connector.get_projects()]
    assert PROJECT_NAME in names


def test_get_projects_returns_project_instances(kitsu_connector):
    assert all(isinstance(p, Project) for p in kitsu_connector.get_projects())


def test_get_project_returns_project_instance(kitsu_connector):
    assert isinstance(kitsu_connector.get_project(PROJECT_NAME), Project)


def test_get_project_correct_name(kitsu_connector):
    assert kitsu_connector.get_project(PROJECT_NAME).name == PROJECT_NAME


def test_get_asset_types_returns_list(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert isinstance(kitsu_connector.get_asset_types(project), list)


def test_get_asset_types_contains_all(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    names = [at.name for at in kitsu_connector.get_asset_types(project)]
    assert all(expected in names for expected in BBB_ASSET_TYPES)


def test_get_asset_types_returns_asset_type_instances(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert all(isinstance(at, AssetType) for at in kitsu_connector.get_asset_types(project))


def test_get_asset_type_returns_asset_type_instance(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert isinstance(kitsu_connector.get_asset_type(project, "Character"), AssetType)


def test_get_asset_type_correct_name(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert kitsu_connector.get_asset_type(project, "Character").name == "Character"


def test_get_assets_returns_list(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    asset_type = kitsu_connector.get_asset_type(project, "Character")
    assert isinstance(kitsu_connector.get_assets(project, asset_type), list)


def test_get_assets_contains_all(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    asset_type = kitsu_connector.get_asset_type(project, "Character")
    names = [a.name for a in kitsu_connector.get_assets(project, asset_type)]
    assert all(expected in names for expected in BBB_ASSETS["Character"])


def test_get_assets_returns_asset_instances(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    asset_type = kitsu_connector.get_asset_type(project, "Character")
    assert all(isinstance(a, Asset) for a in kitsu_connector.get_assets(project, asset_type))


def test_get_asset_returns_asset_instance(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    asset_type = kitsu_connector.get_asset_type(project, "Character")
    assert isinstance(kitsu_connector.get_asset(project, asset_type, "Bunny"), Asset)


def test_get_asset_correct_name(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    asset_type = kitsu_connector.get_asset_type(project, "Character")
    assert kitsu_connector.get_asset(project, asset_type, "Bunny").name == "Bunny"


def test_get_sequences_returns_list(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert isinstance(kitsu_connector.get_sequences(project), list)


def test_get_sequences_contains_all(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    names = [s.name for s in kitsu_connector.get_sequences(project)]
    assert all(expected in names for expected in BBB_SEQUENCES)


def test_get_sequences_returns_sequence_instances(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert all(isinstance(s, Sequence) for s in kitsu_connector.get_sequences(project))


def test_get_sequence_returns_sequence_instance(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert isinstance(kitsu_connector.get_sequence(project, "SQ010"), Sequence)


def test_get_sequence_correct_name(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    assert kitsu_connector.get_sequence(project, "SQ010").name == "SQ010"


def test_get_shots_returns_list(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    sequence = kitsu_connector.get_sequence(project, "SQ010")
    assert isinstance(kitsu_connector.get_shots(project, sequence), list)


def test_get_shots_contains_all(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    sequence = kitsu_connector.get_sequence(project, "SQ010")
    names = [s.name for s in kitsu_connector.get_shots(project, sequence)]
    assert all(expected in names for expected in BBB_SHOTS["SQ010"])


def test_get_shots_returns_shot_instances(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    sequence = kitsu_connector.get_sequence(project, "SQ010")
    assert all(isinstance(s, Shot) for s in kitsu_connector.get_shots(project, sequence))


def test_get_shot_returns_shot_instance(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    sequence = kitsu_connector.get_sequence(project, "SQ010")
    assert isinstance(kitsu_connector.get_shot(project, sequence, "SH010"), Shot)


def test_get_shot_correct_name(kitsu_connector):
    project = kitsu_connector.get_project(PROJECT_NAME)
    sequence = kitsu_connector.get_sequence(project, "SQ010")
    assert kitsu_connector.get_shot(project, sequence, "SH010").name == "SH010"