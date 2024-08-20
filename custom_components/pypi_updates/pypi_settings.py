"""PyPiSettings."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from homeassistant.core import HomeAssistant

from .storage_json import StorageJson


# ------------------------------------------------------
# ------------------------------------------------------
class PypiStatusTypes(Enum):
    """Pypi item."""

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
    """Pypi Base item."""

    def __init__(
        self,
        package_name: str = "",
        version: str = "",
        old_version: str = "",
    ) -> None:
        """Pypi base data.

        Args:
            package_name (str, optional): _description_. Defaults to "".
            version (str, optional): _description_. Defaults to "".
            old_version (str, optional): _description_. Defaults to "".

        """

        self.package_name: str = package_name
        self.version: str = version
        self.old_version: str = old_version


# ------------------------------------------------------
# ------------------------------------------------------
@dataclass
class PyPiItem(PyPiBaseItem):
    """Pypi item."""

    def __init__(
        self,
        package_name: str = "",
        version: str = "",
        old_version: str = "",
        last_update: datetime = datetime.now(),
        status: PypiStatusTypes = PypiStatusTypes.OK,
    ) -> None:
        """Pypi data.

        Args:
            package_name (str, optional): _description_. Defaults to "".
            version (str, optional): _description_. Defaults to "".
            old_version (str, optional): _description_. Defaults to "".
            last_update (datetime, optional): _description_. Defaults to datetime.now().
            status (PypiStatusTypes, optional): _description_. Defaults to PypiStatusTypes.OK.

        """
        super().__init__(package_name, version, old_version)
        self.last_update: datetime = last_update
        self.status: PypiStatusTypes = status


# ------------------------------------------------------
# ------------------------------------------------------
class PyPiSettings(StorageJson):
    """PyPiSettings."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Pypi settings."""

        super().__init__(hass)
        self.pypi_list: list[PyPiItem] = []
