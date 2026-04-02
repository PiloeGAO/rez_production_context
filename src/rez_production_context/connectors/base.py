from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING


class EntityNotFoundError(LookupError):
    """Raised by a connector when a requested entity does not exist."""

if TYPE_CHECKING:
    from rez_production_context.contexts import (
        Asset,
        AssetType,
        Project,
        Sequence,
        Shot,
    )


class Base(ABC):
    """This class provides a basic interface for working with projects and assets.
    It includes methods for retrieving project, asset type, asset, sequence,
    and shot information. Subclasses should implement these methods to provide
    specific functionality.
    """

    def __init__(self, **kwargs) -> None:
        pass

    @classmethod
    def name(cls) -> str:
        return cls.__name__

    @staticmethod
    @abstractmethod
    def available() -> bool:
        """Check if the connector is available or not.

        Returns:
            bool: `True` if the connector is available, `False` otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def get_project(self, project_name: str) -> Project:
        """Retrieve a project by name.

        Args:
            project_name (str): The name of the project.
        Returns:
            Project: The requested project object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_projects(self) -> list[Project]:
        """Retrieve a list of all projects.

        Returns:
            list[Project]: A list of all project objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_asset_type(self, project: Project, asset_type_name: str) -> AssetType:
        """Retrieve an asset type by name within a given project.

        Args:
            project (Project): The project containing the asset type.
            asset_type_name (str): The name of the asset type.

        Returns:
            AssetType: The requested asset type object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_asset_types(self, project: Project) -> list[AssetType]:
        """Retrieve a list of all asset types within a given project.
        Args:
            project (Project): The project containing the asset types.
        Returns:
            list[AssetType]: A list of all asset type objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_asset(
        self, project: Project, asset_type: AssetType, asset_name: str
    ) -> Asset:
        """Retrieve an asset by name within a given project.

        Args:
            project (Project): The project containing the asset.
            asset_type (AssetType): The type of the asset.
            asset_name (str): The name of the asset.
        Returns:
            Asset: The requested asset object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_assets(self, project: Project, asset_type: AssetType) -> list[Asset]:
        """Retrieve a list of all assets within a given project and asset type.

        Args:
            project (Project): The project containing the assets.
            asset_type (AssetType): The type of the assets.

        Returns:
            list[Asset]: A list of all asset objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_sequence(self, project: Project, sequence_name: str) -> Sequence:
        """Retrieve a sequence by name within a given project.

        Args:
            project (Project): The project containing the sequence.
            sequence_name (str): The name of the sequence.

        Returns:
            Sequence: The requested sequence object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_sequences(self, project: Project) -> list[Sequence]:
        """Retrieve a list of all sequences within a given project.

        Args:
            project (Project): The project containing the sequences.

        Returns:
            list[Sequence]: A list of all sequence objects.
        """
        raise NotImplementedError

    @abstractmethod
    def get_shot(self, project: Project, sequence: Sequence, shot_name: str) -> Shot:
        """Retrieve a shot by name within a given project and sequence.

        Args:
            project (Project): The project containing the shot.
            sequence (Sequence): The sequence containing the shot.
            shot_name (str): The name of the shot.

        Returns:
            Shot: The requested shot object.
        """
        raise NotImplementedError

    @abstractmethod
    def get_shots(self, project: Project, sequence: Sequence) -> list[Shot]:
        """Retrieve a list of all shots within a given project and sequence.

        Args:
            project (Project): The project containing the shots.
            sequence (Sequence): The sequence containing the shots.

        Returns:
            list[Shot]: A list of all shot objects.
        """
        raise NotImplementedError
