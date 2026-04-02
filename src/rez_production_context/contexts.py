from .utils import NoInheritInstanceCheck


class ProjectBasedContext(metaclass=NoInheritInstanceCheck):
    def __init__(self, project: "Project"):
        self.__project = project

    @property
    def project(self) -> "Project":
        return self.__project


class AssetTypeBasedContext(ProjectBasedContext):
    def __init__(self, project: "Project", asset_type: "AssetType"):
        super().__init__(project)
        self.__asset_type = asset_type

    @property
    def asset_type(self) -> "AssetType":
        return self.__asset_type


class SequenceBasedContext(ProjectBasedContext):
    def __init__(self, project: "Project", sequence: "Sequence"):
        super().__init__(project)
        self.__sequence = sequence

    @property
    def sequence(self) -> "Sequence":
        return self.__sequence


class Studio:
    def __init__(self, name:str, step: str | None = None):
        self.__name = name
        self.__step = step

    @property
    def name(self) -> str | None:
        return self.__name

    @property
    def step(self) -> str | None:
        return self.__step

    @property
    def projects(self) -> list["Project"]:
        from .manager import Manager

        return Manager().get_projects()


class Project:
    def __init__(self, name: str, step: str | None = None):
        self.__name = name
        self.__step = step

    @property
    def name(self) -> str:
        return self.__name

    @property
    def step(self) -> str | None:
        return self.__step

    @property
    def asset_types(self) -> list["AssetType"]:
        from .manager import Manager

        return Manager().get_asset_types(self)

    @property
    def sequences(self) -> list["Sequence"]:
        from .manager import Manager

        return Manager().get_sequences(self)


class AssetType(ProjectBasedContext):
    def __init__(self, name: str, project: Project, step: str | None = None):
        super().__init__(project)
        self.__name = name
        self.__step = step

    @property
    def name(self) -> str:
        return self.__name

    @property
    def step(self) -> str | None:
        return self.__step

    @property
    def assets(self) -> list["Asset"]:
        from .manager import Manager

        return Manager().get_assets(self.project, self)


class Asset(AssetTypeBasedContext):
    def __init__(self, name: str, asset_type: AssetType, step: str | None = None):
        super().__init__(asset_type.project, asset_type)
        self.__name = name
        self.__step = step

    @property
    def name(self) -> str:
        return self.__name

    @property
    def step(self) -> str | None:
        return self.__step


class Sequence(ProjectBasedContext):
    def __init__(self, name: str, project: Project, step: str | None = None):
        super().__init__(project)
        self.__name = name
        self.__step = step

    @property
    def name(self) -> str:
        return self.__name

    @property
    def step(self) -> str | None:
        return self.__step

    @property
    def shots(self) -> list["Shot"]:
        from .manager import Manager

        return Manager().get_shots(self.project, self)


class Shot(SequenceBasedContext):
    def __init__(self, name: str, sequence: Sequence, step: str | None = None):
        super().__init__(sequence.project, sequence)
        self.__name = name
        self.__step = step

    @property
    def name(self) -> str:
        return self.__name

    @property
    def step(self) -> str | None:
        return self.__step
