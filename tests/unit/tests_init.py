import pytest

from rez_production_context import get_context, get_context_from_env
from rez_production_context.exceptions import EntityNotFoundError
from rez_production_context.constants import (
    CATEGORY_CONTEXT_ENV,
    ENTITY_CONTEXT_ENV,
    PROJECT_CONTEXT_ENV,
    STEP_CONTEXT_ENV,
    STUDIO_CONTEXT_ENV,
)
from rez_production_context.contexts import Asset, AssetType, Project, Sequence, Shot, Studio

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_MANAGER_PATH = "rez_production_context.manager.Manager"

PROJECT_NAME = "Big Buck Bunny"
ASSET_TYPE_NAME = "Character"
ASSET_NAME = "Bunny"
SEQUENCE_NAME = "SQ010"
SHOT_NAME = "SH010"
STEP_NAME = "Rigging"
STUDIO_NAME = "my_studio"


def _make_project():
    return Project(PROJECT_NAME)


def _make_asset_type(project=None):
    return AssetType(ASSET_TYPE_NAME, project or _make_project())


def _make_asset(asset_type=None):
    return Asset(ASSET_NAME, asset_type or _make_asset_type())


def _make_sequence(project=None):
    return Sequence(SEQUENCE_NAME, project or _make_project())


def _make_shot(sequence=None):
    return Shot(SHOT_NAME, sequence or _make_sequence())


# ---------------------------------------------------------------------------
# get_context — validation errors
# ---------------------------------------------------------------------------


def test_get_context_raises_when_category_given_without_project(mocker):
    mocker.patch(MOCK_MANAGER_PATH)
    with pytest.raises(ValueError, match="project is required"):
        get_context(category=ASSET_TYPE_NAME)


def test_get_context_raises_when_entity_given_without_category(mocker):
    mocker.patch(MOCK_MANAGER_PATH)
    with pytest.raises(ValueError, match="category is required"):
        get_context(project=PROJECT_NAME, entity=ASSET_NAME)


# ---------------------------------------------------------------------------
# get_context — return types
# ---------------------------------------------------------------------------


def test_get_context_returns_studio_when_no_args(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    assert isinstance(get_context(), Studio)


def test_get_context_studio_name_defaults_to_studio(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    assert get_context().name == "studio"


def test_get_context_studio_name_is_forwarded(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    assert get_context(studio=STUDIO_NAME).name == STUDIO_NAME


def test_get_context_returns_project(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.get_project.return_value = _make_project()
    assert isinstance(get_context(project=PROJECT_NAME), Project)


def test_get_context_returns_asset_type(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = _make_asset_type(project)
    assert isinstance(get_context(project=PROJECT_NAME, category=ASSET_TYPE_NAME), AssetType)


def test_get_context_returns_sequence_when_asset_type_not_found(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    mgr.get_project.return_value = project
    mgr.get_asset_type.side_effect = EntityNotFoundError("not found")
    mgr.get_sequence.return_value = _make_sequence(project)
    assert isinstance(get_context(project=PROJECT_NAME, category=SEQUENCE_NAME), Sequence)


def test_get_context_returns_asset(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    asset_type = _make_asset_type(project)
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = asset_type
    mgr.get_asset.return_value = _make_asset(asset_type)
    assert isinstance(
        get_context(project=PROJECT_NAME, category=ASSET_TYPE_NAME, entity=ASSET_NAME),
        Asset,
    )


def test_get_context_returns_shot(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    sequence = _make_sequence(project)
    mgr.get_project.return_value = project
    mgr.get_asset_type.side_effect = EntityNotFoundError("not found")
    mgr.get_sequence.return_value = sequence
    mgr.get_shot.return_value = _make_shot(sequence)
    assert isinstance(
        get_context(project=PROJECT_NAME, category=SEQUENCE_NAME, entity=SHOT_NAME),
        Shot,
    )


# ---------------------------------------------------------------------------
# get_context — correct names are forwarded
# ---------------------------------------------------------------------------


def test_get_context_project_name_is_correct(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.get_project.return_value = _make_project()
    assert get_context(project=PROJECT_NAME).name == PROJECT_NAME


def test_get_context_asset_type_name_is_correct(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = _make_asset_type(project)
    assert get_context(project=PROJECT_NAME, category=ASSET_TYPE_NAME).name == ASSET_TYPE_NAME


def test_get_context_asset_name_is_correct(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    asset_type = _make_asset_type(project)
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = asset_type
    mgr.get_asset.return_value = _make_asset(asset_type)
    result = get_context(project=PROJECT_NAME, category=ASSET_TYPE_NAME, entity=ASSET_NAME)
    assert result.name == ASSET_NAME


# ---------------------------------------------------------------------------
# get_context — step is propagated at every level
# ---------------------------------------------------------------------------


def test_get_context_studio_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    assert get_context(step=STEP_NAME).step == STEP_NAME


def test_get_context_project_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.get_project.return_value = _make_project()
    assert get_context(project=PROJECT_NAME, step=STEP_NAME).step == STEP_NAME


def test_get_context_asset_type_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = _make_asset_type(project)
    result = get_context(project=PROJECT_NAME, category=ASSET_TYPE_NAME, step=STEP_NAME)
    assert result.step == STEP_NAME


def test_get_context_sequence_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    mgr.get_project.return_value = project
    mgr.get_asset_type.side_effect = EntityNotFoundError("not found")
    mgr.get_sequence.return_value = _make_sequence(project)
    result = get_context(project=PROJECT_NAME, category=SEQUENCE_NAME, step=STEP_NAME)
    assert result.step == STEP_NAME


def test_get_context_asset_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    asset_type = _make_asset_type(project)
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = asset_type
    mgr.get_asset.return_value = _make_asset(asset_type)
    result = get_context(project=PROJECT_NAME, category=ASSET_TYPE_NAME, entity=ASSET_NAME, step=STEP_NAME)
    assert result.step == STEP_NAME


def test_get_context_shot_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    sequence = _make_sequence(project)
    mgr.get_project.return_value = project
    mgr.get_asset_type.side_effect = EntityNotFoundError("not found")
    mgr.get_sequence.return_value = sequence
    mgr.get_shot.return_value = _make_shot(sequence)
    result = get_context(project=PROJECT_NAME, category=SEQUENCE_NAME, entity=SHOT_NAME, step=STEP_NAME)
    assert result.step == STEP_NAME


# ---------------------------------------------------------------------------
# get_context_from_env
# ---------------------------------------------------------------------------


def test_get_context_from_env_returns_studio_when_no_vars(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    mocker.patch.dict("os.environ", {}, clear=True)
    assert isinstance(get_context_from_env(), Studio)


def test_get_context_from_env_studio_name_defaults_to_studio(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    mocker.patch.dict("os.environ", {}, clear=True)
    assert get_context_from_env().name == "studio"


def test_get_context_from_env_reads_studio_name_from_env(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    mocker.patch.dict("os.environ", {STUDIO_CONTEXT_ENV: STUDIO_NAME}, clear=True)
    assert get_context_from_env().name == STUDIO_NAME


def test_get_context_from_env_returns_project(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.get_project.return_value = _make_project()
    mocker.patch.dict("os.environ", {PROJECT_CONTEXT_ENV: PROJECT_NAME}, clear=True)
    assert isinstance(get_context_from_env(), Project)


def test_get_context_from_env_returns_asset_type(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = _make_asset_type(project)
    mocker.patch.dict(
        "os.environ",
        {PROJECT_CONTEXT_ENV: PROJECT_NAME, CATEGORY_CONTEXT_ENV: ASSET_TYPE_NAME},
        clear=True,
    )
    assert isinstance(get_context_from_env(), AssetType)


def test_get_context_from_env_returns_asset(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    project = _make_project()
    asset_type = _make_asset_type(project)
    mgr.get_project.return_value = project
    mgr.get_asset_type.return_value = asset_type
    mgr.get_asset.return_value = _make_asset(asset_type)
    mocker.patch.dict(
        "os.environ",
        {
            PROJECT_CONTEXT_ENV: PROJECT_NAME,
            CATEGORY_CONTEXT_ENV: ASSET_TYPE_NAME,
            ENTITY_CONTEXT_ENV: ASSET_NAME,
        },
        clear=True,
    )
    assert isinstance(get_context_from_env(), Asset)


def test_get_context_from_env_carries_step(mocker):
    mgr = mocker.patch(MOCK_MANAGER_PATH).return_value
    mgr.studio = Studio("studio")
    mocker.patch.dict("os.environ", {STEP_CONTEXT_ENV: STEP_NAME}, clear=True)
    assert get_context_from_env().step == STEP_NAME


def test_get_context_from_env_raises_when_entity_set_without_category(mocker):
    mocker.patch(MOCK_MANAGER_PATH)
    mocker.patch.dict(
        "os.environ",
        {PROJECT_CONTEXT_ENV: PROJECT_NAME, ENTITY_CONTEXT_ENV: ASSET_NAME},
        clear=True,
    )
    with pytest.raises(ValueError, match="category is required"):
        get_context_from_env()
