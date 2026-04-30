import os

from .constants import CATEGORY_CONTEXT_ENV, ENTITY_CONTEXT_ENV, PROJECT_CONTEXT_ENV, STEP_CONTEXT_ENV, STUDIO_CONTEXT_ENV
from .contexts import Asset, AssetType, Project, Sequence, Shot, Studio

Context = Studio | Project | AssetType | Sequence | Asset | Shot


def get_context(
    studio: str = "studio",
    project: str | None = None,
    category: str | None = None,
    entity: str | None = None,
    step: str | None = None,
) -> Context:
    """Resolve a production context from string identifiers.

    Args:
        studio: Name of the studio. Optional; falls back to ``studio``.
        project: Name of the project. Optional; falls back to ``Studio``.
        category: Name of the asset type or sequence. Requires *project*. Optional.
        entity: Name of the asset or shot. Requires *category*. Optional.
        step: Name of the pipeline step. Optional at every level.

    Returns:
        - ``Studio`` when no arguments are given.
        - ``Project`` when only *project* is given.
        - ``AssetType`` or ``Sequence`` when *project* and *category* are given.
        - ``Asset`` or ``Shot`` when all three are given.

    Raises:
        ValueError: If *category* is given without *project*, or *entity* without *category*.
    """
    if category is not None and project is None:
        raise ValueError("project is required when category is provided.")
    if entity is not None and category is None:
        raise ValueError("category is required when entity is provided.")

    from .exceptions import EntityNotFoundError
    from .manager import Manager

    manager = Manager()
    # Overwrite the private attributes to avoid the user being able to change them manually.
    manager.studio._Studio__name = studio
    manager.studio._Studio__step = step

    if project is None:
        return manager.studio

    project_obj = manager.get_project(project)

    if category is None:
        return Project(project_obj.name, step=step)

    try:
        category_obj = manager.get_asset_type(project_obj, category)
    except EntityNotFoundError:
        category_obj = manager.get_sequence(project_obj, category)

    if entity is None:
        if isinstance(category_obj, AssetType):
            return AssetType(category_obj.name, project_obj, step=step)
        return Sequence(category_obj.name, project_obj, step=step)

    if isinstance(category_obj, AssetType):
        entity_obj = manager.get_asset(project_obj, category_obj, entity)
        return Asset(entity_obj.name, category_obj, step=step)

    entity_obj = manager.get_shot(project_obj, category_obj, entity)
    return Shot(entity_obj.name, category_obj, step=step)


def get_context_from_env() -> Context:
    """Resolve a production context from environment variables.

    All variables are optional; resolution falls back to ``Studio`` when none
    are set. Delegates to :func:`get_context`.
    """
    return get_context(
        os.environ.get(STUDIO_CONTEXT_ENV, "studio"),
        os.environ.get(PROJECT_CONTEXT_ENV),
        os.environ.get(CATEGORY_CONTEXT_ENV),
        os.environ.get(ENTITY_CONTEXT_ENV),
        os.environ.get(STEP_CONTEXT_ENV),
    )