import pytest

from rez_production_context.contexts import (
    Asset,
    AssetType,
    Project,
    Sequence,
    Shot,
    Studio,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_MANAGER_PATH = "rez_production_context.manager.Manager"


def make_project(name="Big Buck Bunny", step=None) -> Project:
    return Project(name, step=step)


def make_asset_type(name="Character", project=None, step=None) -> AssetType:
    return AssetType(name, project or make_project(), step=step)


def make_asset(name="Bunny", asset_type=None, step=None) -> Asset:
    return Asset(name, asset_type or make_asset_type(), step=step)


def make_sequence(name="SQ010", project=None, step=None) -> Sequence:
    return Sequence(name, project or make_project(), step=step)


def make_shot(name="SH010", sequence=None, step=None) -> Shot:
    return Shot(name, sequence or make_sequence(), step=step)


# ---------------------------------------------------------------------------
# ProjectBasedContext
# ---------------------------------------------------------------------------


def test_project_based_context_stores_project():
    project = make_project()
    asset_type = make_asset_type(project=project)
    assert asset_type.project is project


def test_project_based_context_isinstance_is_strict():
    # NoInheritInstanceCheck: isinstance must not match a subclass
    asset_type = make_asset_type()
    from rez_production_context.contexts import ProjectBasedContext

    assert not isinstance(asset_type, ProjectBasedContext)


# ---------------------------------------------------------------------------
# AssetTypeBasedContext
# ---------------------------------------------------------------------------


def test_asset_type_based_context_stores_asset_type():
    asset_type = make_asset_type()
    asset = make_asset(asset_type=asset_type)
    assert asset.asset_type is asset_type


def test_asset_type_based_context_exposes_project_via_base():
    project = make_project()
    asset_type = make_asset_type(project=project)
    asset = make_asset(asset_type=asset_type)
    assert asset.project is project


# ---------------------------------------------------------------------------
# SequenceBasedContext
# ---------------------------------------------------------------------------


def test_sequence_based_context_stores_sequence():
    sequence = make_sequence()
    shot = make_shot(sequence=sequence)
    assert shot.sequence is sequence


def test_sequence_based_context_exposes_project_via_base():
    project = make_project()
    sequence = make_sequence(project=project)
    shot = make_shot(sequence=sequence)
    assert shot.project is project


# ---------------------------------------------------------------------------
# Studio
# ---------------------------------------------------------------------------


def test_studio_stores_name():
    assert Studio("my_studio").name == "my_studio"


def test_studio_name_defaults_to_studio():
    assert Studio("studio").name == "studio"


def test_studio_step_is_none_by_default():
    assert Studio("studio").step is None


def test_studio_stores_step():
    assert Studio("studio", step="Rigging").step == "Rigging"


def test_studio_projects_delegates_to_manager(mocker):
    expected = [make_project("BBB"), make_project("Elephants Dream")]
    MockManager = mocker.patch(MOCK_MANAGER_PATH)
    MockManager.return_value.get_projects.return_value = expected
    assert Studio("studio").projects == expected


# ---------------------------------------------------------------------------
# Project
# ---------------------------------------------------------------------------


def test_project_stores_name():
    assert make_project("Big Buck Bunny").name == "Big Buck Bunny"


def test_project_step_is_none_by_default():
    assert make_project().step is None


def test_project_stores_step():
    assert make_project(step="Rigging").step == "Rigging"


def test_project_asset_types_delegates_to_manager(mocker):
    project = make_project()
    expected = [make_asset_type(project=project)]
    MockManager = mocker.patch(MOCK_MANAGER_PATH)
    MockManager.return_value.get_asset_types.return_value = expected
    assert project.asset_types == expected
    MockManager.return_value.get_asset_types.assert_called_once_with(project)


def test_project_sequences_delegates_to_manager(mocker):
    project = make_project()
    expected = [make_sequence(project=project)]
    MockManager = mocker.patch(MOCK_MANAGER_PATH)
    MockManager.return_value.get_sequences.return_value = expected
    assert project.sequences == expected
    MockManager.return_value.get_sequences.assert_called_once_with(project)


# ---------------------------------------------------------------------------
# AssetType
# ---------------------------------------------------------------------------


def test_asset_type_stores_name():
    assert make_asset_type("Character").name == "Character"


def test_asset_type_step_is_none_by_default():
    assert make_asset_type().step is None


def test_asset_type_stores_step():
    assert make_asset_type(step="Rigging").step == "Rigging"


def test_asset_type_stores_project():
    project = make_project()
    assert make_asset_type(project=project).project is project


def test_asset_type_assets_delegates_to_manager(mocker):
    project = make_project()
    asset_type = make_asset_type(project=project)
    expected = [make_asset(asset_type=asset_type)]
    MockManager = mocker.patch(MOCK_MANAGER_PATH)
    MockManager.return_value.get_assets.return_value = expected
    assert asset_type.assets == expected
    MockManager.return_value.get_assets.assert_called_once_with(project, asset_type)


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------


def test_asset_stores_name():
    assert make_asset("Bunny").name == "Bunny"


def test_asset_step_is_none_by_default():
    assert make_asset().step is None


def test_asset_stores_step():
    assert make_asset(step="Rigging").step == "Rigging"


def test_asset_inherits_asset_type():
    asset_type = make_asset_type()
    assert make_asset(asset_type=asset_type).asset_type is asset_type


def test_asset_inherits_project_from_asset_type():
    project = make_project()
    asset_type = make_asset_type(project=project)
    assert make_asset(asset_type=asset_type).project is project


# ---------------------------------------------------------------------------
# Sequence
# ---------------------------------------------------------------------------


def test_sequence_stores_name():
    assert make_sequence("SQ010").name == "SQ010"


def test_sequence_step_is_none_by_default():
    assert make_sequence().step is None


def test_sequence_stores_step():
    assert make_sequence(step="Layout").step == "Layout"


def test_sequence_stores_project():
    project = make_project()
    assert make_sequence(project=project).project is project


def test_sequence_shots_delegates_to_manager(mocker):
    project = make_project()
    sequence = make_sequence(project=project)
    expected = [make_shot(sequence=sequence)]
    MockManager = mocker.patch(MOCK_MANAGER_PATH)
    MockManager.return_value.get_shots.return_value = expected
    assert sequence.shots == expected
    MockManager.return_value.get_shots.assert_called_once_with(project, sequence)


# ---------------------------------------------------------------------------
# Shot
# ---------------------------------------------------------------------------


def test_shot_stores_name():
    assert make_shot("SH010").name == "SH010"


def test_shot_step_is_none_by_default():
    assert make_shot().step is None


def test_shot_stores_step():
    assert make_shot(step="Animation").step == "Animation"


def test_shot_inherits_sequence():
    sequence = make_sequence()
    assert make_shot(sequence=sequence).sequence is sequence


def test_shot_inherits_project_from_sequence():
    project = make_project()
    sequence = make_sequence(project=project)
    assert make_shot(sequence=sequence).project is project
