""" PyPiSettings """
from .settings_json import SettingsJson
from datetime import datetime
from enum import Enum
from dataclasses import dataclass


# ------------------------------------------------------
# ------------------------------------------------------
class PypiStatusTypes(Enum):
    """Pypi item"""

    OK = 0
    UPDATED = 1
    FETCH_TIMEOUT = 2
    NOT_FOUND = 3
    TIMEOUT = 4
    CONNECT_ERROR = 5


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class PyPiBaseItem:
    """Pypi Base item"""

    def __init__(
        self,
        package_name: str = "",
        version: str = "",
        old_version: str = "",
    ) -> None:
        self.package_name: str = package_name
        self.version: str = version
        self.old_version: str = old_version


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class PyPiItem(PyPiBaseItem):
    """Pypi item"""

    def __init__(
        self,
        package_name: str = "",
        version: str = "",
        old_version: str = "",
        last_update: datetime = datetime.now(),
        status: PypiStatusTypes = PypiStatusTypes.OK,
    ) -> None:
        super().__init__(package_name, version, old_version)
        self.last_update: datetime = last_update
        self.status: PypiStatusTypes = status


# ------------------------------------------------------
# ------------------------------------------------------
class PyPiSettings(SettingsJson):
    """PyPiSettings"""

    def __init__(self) -> None:
        self.pypi_list: list[PyPiItem] = []
