import importlib

from ..contexts import Asset, AssetType, Project, Sequence, Shot
from .base import Base, EntityNotFoundError


class Shotgun(Base):
    """Connector for ShotGrid (Flow Production Tracking) using the shotgun_api3 library.

    Asset types are not a first-class entity in ShotGrid — they are stored as
    the ``sg_asset_type`` string field on each ``Asset`` record. The connector
    derives ``AssetType`` objects by collecting the distinct values found on
    assets within the requested project.
    """

    def __init__(self, url: str, script_name: str, api_key: str, **kwargs):
        """Connect to a ShotGrid server using script-based authentication.

        Args:
            url: URL of the ShotGrid site (e.g. ``https://studio.shotgunstudio.com``).
            script_name: Name of the API script registered in ShotGrid.
            api_key: API key associated with the script.
        """
        super().__init__(**kwargs)

        self.server_address = url
        self._sg_instance = self._sg().Shotgun(
            url, script_name=script_name, api_key=api_key
        )

    @classmethod
    def _sg(cls):
        """Return the shotgun_api3 module, relying on ``sys.modules`` caching."""
        return importlib.import_module("shotgun_api3")

    def _connection(self):
        """Return the active ShotGrid connection instance."""
        return self._sg_instance

    @staticmethod
    def available() -> bool:
        """Check if ``shotgun_api3`` is available."""
        try:
            importlib.import_module("shotgun_api3")
            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_sg_project(self, project: Project) -> dict:
        """Return the raw ShotGrid project record matching ``project.name``."""
        result = self._connection().find_one(
            "Project",
            [["code", "is", project.name]],
            ["id"],
        )
        if result is None:
            raise EntityNotFoundError(f"Project '{project.name}' not found.")
        return result

    def _find_sg_sequence(self, project: Project, sequence: Sequence) -> dict:
        """Return the raw ShotGrid sequence record matching ``sequence.name``."""
        sg_project = self._find_sg_project(project)
        result = self._connection().find_one(
            "Sequence",
            [
                ["project", "is", {"type": "Project", "id": sg_project["id"]}],
                ["code", "is", sequence.name],
            ],
            ["id"],
        )
        if result is None:
            raise EntityNotFoundError(f"Sequence '{sequence.name}' not found in project '{project.name}'.")
        return result

    # ------------------------------------------------------------------
    # Projects
    # ------------------------------------------------------------------

    def get_projects(self) -> list[Project]:
        """Return all active projects."""
        results = self._connection().find("Project", [], ["code"])
        return [Project(result["code"]) for result in results]

    def get_project(self, project_name: str) -> Project:
        """Return the project matching ``project_name``.

        Args:
            project_name: Name of the project to retrieve.
        """
        result = self._connection().find_one(
            "Project",
            [["code", "is", project_name]],
            ["code"],
        )
        if result is None:
            raise EntityNotFoundError(f"Project '{project_name}' not found.")
        return Project(result["code"])

    # ------------------------------------------------------------------
    # Asset types
    # ------------------------------------------------------------------

    def get_asset_types(self, project: Project) -> list[AssetType]:
        """Return all asset types within ``project``.

        Asset types are derived from the distinct ``sg_asset_type`` values
        found on asset records, as ShotGrid has no dedicated entity for them.

        Args:
            project: The project to query.
        """
        sg_project = self._find_sg_project(project)
        assets = self._connection().find(
            "Asset",
            [["project", "is", {"type": "Project", "id": sg_project["id"]}]],
            ["sg_asset_type"],
        )
        seen = set()
        asset_types = []
        for asset in assets:
            name = asset["sg_asset_type"]
            if name and name not in seen:
                seen.add(name)
                asset_types.append(AssetType(name, project))
        return asset_types

    def get_asset_type(self, project: Project, asset_type_name: str) -> AssetType:
        """Return an asset type by name within ``project``.

        Args:
            project: The project the asset type belongs to.
            asset_type_name: Name of the asset type to retrieve.
        """
        return AssetType(asset_type_name, project)

    # ------------------------------------------------------------------
    # Assets
    # ------------------------------------------------------------------

    def get_assets(self, project: Project, asset_type: AssetType) -> list[Asset]:
        """Return all assets of ``asset_type`` within ``project``.

        Args:
            project: The project to query.
            asset_type: The asset type to filter by.
        """
        sg_project = self._find_sg_project(project)
        results = self._connection().find(
            "Asset",
            [
                ["project", "is", {"type": "Project", "id": sg_project["id"]}],
                ["sg_asset_type", "is", asset_type.name],
            ],
            ["code"],
        )
        return [Asset(result["code"], asset_type) for result in results]

    def get_asset(
        self, project: Project, asset_type: AssetType, asset_name: str
    ) -> Asset:
        """Return the asset matching ``asset_name`` within ``project`` and ``asset_type``.

        Args:
            project: The project containing the asset.
            asset_type: The asset type the asset belongs to.
            asset_name: Name of the asset to retrieve.
        """
        sg_project = self._find_sg_project(project)
        result = self._connection().find_one(
            "Asset",
            [
                ["project", "is", {"type": "Project", "id": sg_project["id"]}],
                ["sg_asset_type", "is", asset_type.name],
                ["code", "is", asset_name],
            ],
            ["code"],
        )
        if result is None:
            raise EntityNotFoundError(f"Asset '{asset_name}' not found in project '{project.name}'.")
        return Asset(result["code"], asset_type)

    # ------------------------------------------------------------------
    # Sequences
    # ------------------------------------------------------------------

    def get_sequences(self, project: Project) -> list[Sequence]:
        """Return all sequences within ``project``.

        Args:
            project: The project to query.
        """
        sg_project = self._find_sg_project(project)
        results = self._connection().find(
            "Sequence",
            [["project", "is", {"type": "Project", "id": sg_project["id"]}]],
            ["code"],
        )
        return [Sequence(result["code"], project) for result in results]

    def get_sequence(self, project: Project, sequence_name: str) -> Sequence:
        """Return the sequence matching ``sequence_name`` within ``project``.

        Args:
            project: The project containing the sequence.
            sequence_name: Name of the sequence to retrieve.
        """
        sg_project = self._find_sg_project(project)
        result = self._connection().find_one(
            "Sequence",
            [
                ["project", "is", {"type": "Project", "id": sg_project["id"]}],
                ["code", "is", sequence_name],
            ],
            ["code"],
        )
        if result is None:
            raise EntityNotFoundError(f"Sequence '{sequence_name}' not found in project '{project.name}'.")
        return Sequence(result["code"], project)

    # ------------------------------------------------------------------
    # Shots
    # ------------------------------------------------------------------

    def get_shots(self, project: Project, sequence: Sequence) -> list[Shot]:
        """Return all shots within ``sequence``.

        Args:
            project: The project containing the sequence.
            sequence: The sequence to query.
        """
        sg_project = self._find_sg_project(project)
        sg_sequence = self._find_sg_sequence(project, sequence)
        results = self._connection().find(
            "Shot",
            [
                ["project", "is", {"type": "Project", "id": sg_project["id"]}],
                ["sg_sequence", "is", {"type": "Sequence", "id": sg_sequence["id"]}],
            ],
            ["code"],
        )
        return [Shot(result["code"], sequence) for result in results]

    def get_shot(self, project: Project, sequence: Sequence, shot_name: str) -> Shot:
        """Return the shot matching ``shot_name`` within ``sequence``.

        Args:
            project: The project containing the sequence.
            sequence: The sequence containing the shot.
            shot_name: Name of the shot to retrieve.
        """
        sg_project = self._find_sg_project(project)
        sg_sequence = self._find_sg_sequence(project, sequence)
        result = self._connection().find_one(
            "Shot",
            [
                ["project", "is", {"type": "Project", "id": sg_project["id"]}],
                ["sg_sequence", "is", {"type": "Sequence", "id": sg_sequence["id"]}],
                ["code", "is", shot_name],
            ],
            ["code"],
        )
        if result is None:
            raise EntityNotFoundError(f"Shot '{shot_name}' not found in sequence '{sequence.name}'.")
        return Shot(result["code"], sequence)
