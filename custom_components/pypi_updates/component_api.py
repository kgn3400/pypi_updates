""" ------------------------------------------------------------------
------------------------------------------------------------------"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from aiohttp.client import ClientConnectionError, ClientSession
import async_timeout

from homeassistant.core import ServiceCall
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import LOGGER
from .pypi_settings import PyPiBaseItem, PyPiItem, PyPiSettings, PypiStatusTypes


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Pypi updates interface"""

    def __init__(
        self,
        session: ClientSession | None,
        pypi_list: list[str],
        hours_between_updates: int,
        clear_updates_after_hours: int,
    ) -> None:
        self.session: ClientSession | None = session
        self.pypi_list: list[str] = pypi_list
        self.hours_between_updates: int = hours_between_updates
        self.clear_updates_after_hours: int = clear_updates_after_hours

        self.close_session: bool = False
        self.first_time: bool = True
        self.updates: bool = False
        """Any updates in pypi list binary sensor"""
        self.pypi_updates: list[PyPiBaseItem] = []
        self.markdown: str = ""
        self.last_full_update: datetime = datetime.now()
        self.coordinator: DataUpdateCoordinator

        self.settings: PyPiSettings = PyPiSettings()
        self.settings.read_settings()

    # ------------------------------------------------------------------
    async def startup(self) -> None:
        """Pypi startup"""
        await self.sync_lists()

    # ------------------------------------------------------------------
    async def sync_lists(self) -> None:
        """Pypi startup"""

        save_settings: bool = False

        def sort_key(item: PyPiItem) -> str:
            return item.package_name

        # Delete part
        for index, item in reversed(list(enumerate(self.settings.pypi_list))):
            if item.package_name not in self.pypi_list:
                save_settings = True
                del self.settings.pypi_list[index]

        # Add new items
        cur_package: list = [itemx.package_name for itemx in self.settings.pypi_list]

        for itemy in self.pypi_list:
            if itemy not in cur_package:
                save_settings = True

                self.settings.pypi_list.append(
                    PyPiItem(itemy, status=PypiStatusTypes.OK)
                )

        if save_settings:
            self.settings.pypi_list.sort(key=sort_key)
            self.settings.write_settings()

    # ------------------------------------------------------------------
    async def reset_service(self, call: ServiceCall) -> None:
        """Pypi reset service"""

        for item in self.settings.pypi_list:
            if item.status == PypiStatusTypes.UPDATED:
                item.status = PypiStatusTypes.OK

        self.settings.write_settings()
        await self.go_update()

    # ------------------------------------------------------------------
    async def update_service(self, call: ServiceCall) -> None:
        """Pypi updates service"""

        await self.go_update(True)
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def go_update(self, force_update: bool = False) -> None:
        """Go updates"""

        if (
            force_update
            or (self.last_full_update + timedelta(hours=self.hours_between_updates))
            < datetime.now()
        ):
            await self.check_pypi_for_update()
            self.last_full_update = datetime.now()

        await self.check_update_status()
        await self.create_markdown()

    # ------------------------------------------------------------------
    async def update(self) -> None:
        """Update"""
        if self.first_time:
            self.first_time = False
            await self.startup()
            await self.go_update(True)
        else:
            await self.go_update()

    # ------------------------------------------------------------------
    async def create_markdown(self) -> None:
        """Create markdown"""
        if self.updates:
            tmp_md: str = (
                "### <font color= dodgerblue>"
                '  <ha-icon icon="mdi:package-variant"></ha-icon></font>'
                " Pypi package updates\r"
            )
            for item in self.pypi_updates:
                tmp_md += (
                    f"- [{item.package_name.capitalize()}"
                    f"](https://www.pypi.org/project/{item.package_name}"
                    f") updated to version **{item.version}"
                    f"** from {item.old_version}\r"
                )
            self.markdown = tmp_md
        else:
            self.markdown = (
                "### <font color= dodgerblue>"
                '  <ha-icon icon="mdi:package-variant"></ha-icon></font> Pypi package updates\r'
                "- No updates"
            )

    # ------------------------------------------------------------------
    async def check_update_status(self) -> None:
        """Check updates status"""
        tmp_updates: bool = False
        self.pypi_updates.clear()

        for item in self.settings.pypi_list:
            if (
                item.status == PypiStatusTypes.UPDATED
                and (item.last_update + timedelta(hours=self.clear_updates_after_hours))
                < datetime.now()
            ):
                item.status = PypiStatusTypes.OK
            elif item.status == PypiStatusTypes.UPDATED:
                self.pypi_updates.append(
                    PyPiBaseItem(
                        item.package_name,
                        item.version,
                        item.old_version,
                    )
                )
                tmp_updates = True

        self.updates = tmp_updates

    # ------------------------------------------------------------------
    async def check_pypi_for_update(self) -> None:
        """Check pypi updates"""

        save_settings: bool = False

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        for item in self.settings.pypi_list:
            try:
                version = await self.get_package_version(item.package_name)

                #  First check ?
                if item.version == "":
                    save_settings = True
                    item.version = version
                    item.last_update = datetime.now()
                    item.status = PypiStatusTypes.OK

                elif item.version != version:
                    save_settings = True
                    item.old_version = item.version
                    item.version = version
                    item.last_update = datetime.now()
                    item.status = PypiStatusTypes.UPDATED

            except asyncio.TimeoutError:
                item.status = PypiStatusTypes.FETCH_TIMEOUT
            except NotFoundException:
                item.status = PypiStatusTypes.NOT_FOUND
            except ClientConnectionError:
                item.status = PypiStatusTypes.CONNECT_ERROR
                LOGGER.exception("Client connect error")

        if save_settings:
            self.settings.write_settings()

        if self.session and self.close_session:
            await self.session.close()

    # ------------------------------------------------------------------
    async def get_package_version(self, package: str) -> str:
        """Pypi package version"""
        # https://pypi.org/pypi/pypiserver/json
        # https://pypi.org/project/pypiserver/

        json_dict: dict = {}

        async with async_timeout.timeout(5):
            response = await self.session.request(  # type: ignore
                "GET", "https://pypi.org/pypi/" + package + "/json"
            )
            json_dict = json.loads(await response.text())

        if "message" in json_dict and json_dict["message"] == "Not Found":
            raise NotFoundException()

        return json_dict["info"]["version"]


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class NotFoundException(Exception):
    """Not found exception"""


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class FindPyPiPackage:
    """Find Pypi package interface"""

    # ------------------------------------------------------------------
    async def exist(self, session: ClientSession | None, package: str) -> bool:
        """Pypi package exist"""
        close_session: bool = False
        ret_val: bool = True
        json_dict: dict = {}

        if session is None:
            session = ClientSession()
            close_session = True

        try:
            async with async_timeout.timeout(5):
                response = await session.request(
                    "GET", "https://pypi.org/pypi/" + package + "/json"
                )
                json_dict = json.loads(await response.text())

        except asyncio.TimeoutError:
            ret_val = False

        if "message" in json_dict and json_dict["message"] == "Not Found":
            ret_val = False
        # https://pypi.org/pypi/pypiserver/json
        # https://pypi.org/project/pypiserver/
        # return json_dict["info"]["version"]

        if session and close_session:
            await session.close()

        return ret_val
