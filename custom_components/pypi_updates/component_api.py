""" ------------------------------------------------------------------
------------------------------------------------------------------"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiohttp.client import ClientSession, ClientConnectionError
import async_timeout
from homeassistant.core import ServiceCall
import json
from .pypi_settings import PyPiSettings, PyPiItem, PypiStatusTypes
from .const import LOGGER


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
        self.markdown: str = ""
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
        for num in range(len(self.settings.pypi_list) - 1, -1, -1):
            item: PyPiItem = self.settings.pypi_list[num]

            if item.package_name not in self.pypi_list:
                save_settings = True
                del self.settings.pypi_list[num]

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
    async def update_service(self, call: ServiceCall) -> None:
        """Pypi updates service"""

        await self.go_update()

    # ------------------------------------------------------------------
    async def go_update(self) -> None:
        """Pypi go updates"""
        await self.check_pypi_for_update()
        await self.check_update_status()
        await self.create_markdown()

    # ------------------------------------------------------------------
    async def update(self) -> None:
        """Update"""
        if self.first_time:
            self.first_time = False
            await self.startup()

        await self.go_update()

    # ------------------------------------------------------------------
    async def create_markdown(self) -> None:
        """Check updates status"""
        if self.updates:
            tmp_md: str = (
                "### <font color= dodgerblue>"
                + '  <ha-icon icon="mdi:package-variant"></ha-icon></font> Pypi package updates\r'
            )
            for item in self.settings.pypi_list:
                if item.status == PypiStatusTypes.UPDATED:
                    tmp_md += (
                        "- ["
                        + item.package_name.capitalize()
                        + "](https://www.pypi.org/project/"
                        + item.package_name
                        + ") updated to version **"
                        + item.version
                        + "** from "
                        + item.old_version
                        + "\r"
                    )
            self.markdown = tmp_md
        else:
            self.markdown = (
                "### <font color= dodgerblue>"
                + '  <ha-icon icon="mdi:package-variant"></ha-icon></font> Pypi package updates\r'
                + "- No updates"
            )

    # ------------------------------------------------------------------
    async def check_update_status(self) -> None:
        """Check updates status"""
        tmp_updates: bool = False

        for item in self.settings.pypi_list:
            if (
                item.status == PypiStatusTypes.UPDATED
                and (item.last_update + timedelta(hours=self.clear_updates_after_hours))
                < datetime.now()
            ):
                item.status = PypiStatusTypes.OK
            elif item.status == PypiStatusTypes.UPDATED:
                tmp_updates = True

        if tmp_updates:
            self.updates = True

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
