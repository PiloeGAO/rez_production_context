import importlib

from ..contexts import Asset, AssetType, Project, Sequence, Shot
from ..exceptions import EntityNotFoundError
from .base import Base


class Kitsu(Base):
    """Connector for Kitsu using the gazu client library.

    Authenticates as a bot account on initialisation and exposes the full
    production hierarchy through the standard ``Base`` interface.
    ``gazu`` is imported lazily so the connector can be loaded even when the
    package is not installed — ``available()`` will simply return ``False``.
    """

    def __init__(self, url: str, api_key: str, email: str | None = None, **kwargs):
        """Connect to a Kitsu server and open a session.

        Args:
            url: Base URL of the Kitsu server (e.g. ``http://localhost:8080``).
            api_key: API key of the bot account, or password for standard user accounts (not recommended).
            email: Email address used to log in. When omitted, ``api_key`` is used as a JWT token.
        """
        super().__init__(**kwargs)

        self.server_address = url

        self._gazu().set_host(url)

        if not email:
            self._gazu().set_token(api_key)
        else:
            self._gazu().log_in(email, api_key)

    @classmethod
    def _gazu(cls):
        """Return the gazu module, relying on ``sys.modules`` caching."""
        return importlib.import_module("gazu")

    @staticmethod
    def available() -> bool:
        """Check if `gazu` is available."""
        try:
            importlib.import_module("gazu")
            return True
        except ImportError:
            return False

    def get_projects(self) -> list[Project]:
        """Return all projects visible to the authenticated bot account."""
        return [
            Project(project["name"]) for project in self._gazu().project.all_projects()
        ]

    def get_project(self, project_name: str) -> Project:
        """Return the project matching ``project_name``.

        Args:
            project_name: Name of the project to retrieve.
        """
        project = self._gazu().project.get_project_by_name(project_name)
        if project is None:
            raise EntityNotFoundError(f"Project '{project_name}' not found.")
        return Project(project["name"])

    def get_asset_types(self, project: Project) -> list[AssetType]:
        """Return all asset types defined in ``project``.

        Args:
            project: The project to query.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        return [
            AssetType(asset_type["name"], project)
            for asset_type in self._gazu().asset.all_asset_types_for_project(
                gazu_project
            )
        ]

    def get_asset_type(self, project: Project, asset_type_name: str) -> AssetType:
        """Return the asset type matching ``asset_type_name`` within ``project``.

        Args:
            project: The project the asset type belongs to.
            asset_type_name: Name of the asset type to retrieve.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        asset_types = self._gazu().asset.all_asset_types_for_project(gazu_project)
        for asset_type in asset_types:
            if asset_type["name"] == asset_type_name:
                return AssetType(asset_type["name"], project)
        raise EntityNotFoundError(
            f"Asset type '{asset_type_name}' not found in project '{project.name}'."
        )

    def get_assets(self, project: Project, asset_type: AssetType) -> list[Asset]:
        """Return all assets of ``asset_type`` within ``project``.

        Args:
            project: The project to query.
            asset_type: The asset type to filter by.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        gazu_asset_type = self._gazu().asset.get_asset_type_by_name(asset_type.name)
        return [
            Asset(asset["name"], asset_type)
            for asset in self._gazu().asset.all_assets_for_project_and_type(
                gazu_project, gazu_asset_type
            )
        ]

    def get_asset(
        self, project: Project, asset_type: AssetType, asset_name: str
    ) -> Asset:
        """Return the asset matching ``asset_name`` within ``project``.

        Args:
            project: The project containing the asset.
            asset_type: The asset type the asset belongs to.
            asset_name: Name of the asset to retrieve.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        asset = self._gazu().asset.get_asset_by_name(gazu_project, asset_name)
        if asset is None:
            raise EntityNotFoundError(f"Asset '{asset_name}' not found in project '{project.name}'.")
        return Asset(asset["name"], asset_type)

    def get_sequences(self, project: Project) -> list[Sequence]:
        """Return all sequences within ``project``.

        Args:
            project: The project to query.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        return [
            Sequence(sequence["name"], project)
            for sequence in self._gazu().shot.all_sequences_for_project(gazu_project)
        ]

    def get_sequence(self, project: Project, sequence_name: str) -> Sequence:
        """Return the sequence matching ``sequence_name`` within ``project``.

        Args:
            project: The project containing the sequence.
            sequence_name: Name of the sequence to retrieve.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        sequence = self._gazu().shot.get_sequence_by_name(gazu_project, sequence_name)
        if sequence is None:
            raise EntityNotFoundError(f"Sequence '{sequence_name}' not found in project '{project.name}'.")
        return Sequence(sequence["name"], project)

    def get_shots(self, project: Project, sequence: Sequence) -> list[Shot]:
        """Return all shots within ``sequence``.

        Args:
            project: The project containing the sequence.
            sequence: The sequence to query.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        gazu_sequence = self._gazu().shot.get_sequence_by_name(
            gazu_project, sequence.name
        )
        return [
            Shot(shot["name"], sequence)
            for shot in self._gazu().shot.all_shots_for_sequence(gazu_sequence)
        ]

    def get_shot(self, project: Project, sequence: Sequence, shot_name: str) -> Shot:
        """Return the shot matching ``shot_name`` within ``sequence``.

        Args:
            project: The project containing the sequence.
            sequence: The sequence containing the shot.
            shot_name: Name of the shot to retrieve.
        """
        gazu_project = self._gazu().project.get_project_by_name(project.name)
        gazu_sequence = self._gazu().shot.get_sequence_by_name(
            gazu_project, sequence.name
        )
        shot = self._gazu().shot.get_shot_by_name(gazu_sequence, shot_name)
        if shot is None:
            raise EntityNotFoundError(f"Shot '{shot_name}' not found in sequence '{sequence.name}'.")
        return Shot(shot["name"], sequence)
