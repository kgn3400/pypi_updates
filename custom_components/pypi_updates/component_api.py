"""Component api."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from aiohttp.client import ClientConnectionError, ClientSession
import orjson

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.template import Template
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_MD_HEADER_TEMPLATE,
    CONF_MD_ITEM_TEMPLATE,
    CONF_MD_NO_UPDATES_TEMPLATE,
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
    TRANSLATION_KEY_TEMPLATE_ERROR,
)
from .pypi_settings import PyPiBaseItem, PyPiItem, PyPiSettings, PypiStatusTypes


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class ComponentApi:
    """Pypi updates interface."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        session: ClientSession | None,
        pypi_list: list[str],
        hours_between_updates: int,
        clear_updates_after_hours: int,
    ) -> None:
        """Component api."""

        self.hass = hass
        self.entry: ConfigEntry = entry
        self.session: ClientSession | None = session
        self.pypi_list: list[str] = pypi_list
        self.hours_between_updates: int = hours_between_updates
        self.clear_updates_after_hours: int = clear_updates_after_hours

        self.entity_id: str = ""
        self.close_session: bool = False
        self.first_time: bool = True
        self.updates: bool = False
        self.pypi_updates: list[PyPiBaseItem] = []
        self.last_pypi_update: PyPiBaseItem = PyPiBaseItem()
        self.markdown: str = ""
        self.last_full_update: datetime = datetime.now()
        self.coordinator: DataUpdateCoordinator
        self.last_error_template: str = ""
        self.last_error_txt_template: str = ""

        self.settings: PyPiSettings = PyPiSettings()

    # ------------------------------------------------------------------
    async def async_startup(self) -> None:
        """Pypi startup."""
        await self.settings.async_read_settings(
            self.hass.config.path(STORAGE_DIR, DOMAIN)
        )

        await self.async_sync_lists()

    # ------------------------------------------------------------------
    async def async_sync_lists(self) -> None:
        """Sync lists."""

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
            await self.settings.async_write_settings()

    # ------------------------------------------------------------------
    async def async_reset_service(self, call: ServiceCall) -> None:
        """Pypi reset service."""

        for item in self.settings.pypi_list:
            if item.status == PypiStatusTypes.UPDATED:
                item.status = PypiStatusTypes.OK

        await self.settings.async_write_settings()
        await self.async_go_update()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_update_service(self, call: ServiceCall) -> None:
        """Pypi updates service."""

        await self.async_go_update(True)
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_go_update(self, force_update: bool = False) -> None:
        """Go updates."""

        if (
            force_update
            or (self.last_full_update + timedelta(hours=self.hours_between_updates))
            < datetime.now()
        ):
            await self.async_check_pypi_for_update()
            self.last_full_update = datetime.now()

        await self.async_check_update_status()
        await self.async_create_markdown()

    # ------------------------------------------------------------------
    async def async_update(self) -> None:
        """Update."""
        if self.first_time:
            self.first_time = False
            await self.async_startup()
            await self.async_go_update(True)
        else:
            await self.async_go_update()

    # ------------------------------------------------------------------
    async def async_create_markdown(self) -> None:
        """Create markdown."""

        try:
            if self.updates:
                tmp_md: str = ""
                values: dict[str, Any] = {}

                if self.entry.options.get(CONF_MD_HEADER_TEMPLATE, "") != "":
                    value_template: Template | None = Template(
                        str(self.entry.options.get(CONF_MD_HEADER_TEMPLATE, "")),
                        self.hass,
                    )

                    tmp_md = value_template.async_render({})

                for item in self.pypi_updates:
                    value_template: Template | None = Template(
                        str(self.entry.options.get(CONF_MD_ITEM_TEMPLATE, "")),
                        self.hass,
                    )
                    values = {
                        "package_name": item.package_name.capitalize(),
                        "version": item.version,
                        "old_version": item.old_version,
                    }
                    tmp_md += value_template.async_render(values)

                self.markdown = tmp_md.replace("<br>", "\r")
            else:
                value_template: Template | None = Template(
                    str(self.entry.options.get(CONF_MD_NO_UPDATES_TEMPLATE, "")),
                    self.hass,
                )

                self.markdown = str(value_template.async_render({})).replace(
                    "<br>", "\r"
                )

        except (TypeError, TemplateError) as e:
            await self.async_create_issue_template(
                str(e), value_template.template, TRANSLATION_KEY_TEMPLATE_ERROR
            )

    # ------------------------------------------------------------------
    async def async_create_issue_template(
        self,
        error_txt: str,
        template: str,
        translation_key: str,
    ) -> None:
        """Create issue on entity."""

        if (
            self.last_error_template != template
            or error_txt != self.last_error_txt_template
        ):
            LOGGER.warning(error_txt)

            ir.async_create_issue(
                self.hass,
                DOMAIN,
                DOMAIN_NAME + datetime.now().isoformat(),
                issue_domain=DOMAIN,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=translation_key,
                translation_placeholders={
                    "error_txt": error_txt,
                    "template": template,
                },
            )
            self.last_error_template = template
            self.last_error_txt_template = error_txt

    # ------------------------------------------------------------------
    async def async_check_update_status(self) -> None:
        """Check updates status."""
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

                self.last_pypi_update = PyPiBaseItem(
                    item.package_name,
                    item.version,
                    item.old_version,
                )

                #  Does this work ?
                if self.entity_id:
                    self.hass.states.async_set(
                        self.entity_id,
                        STATE_OFF,
                        force_update=True,
                    )
                tmp_updates = True

        self.updates = tmp_updates

    # ------------------------------------------------------------------
    async def async_check_pypi_for_update(self) -> None:
        """Check pypi updates."""

        save_settings: bool = False

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        for item in self.settings.pypi_list:
            try:
                version = await self.async_get_package_version(item.package_name)

                #  First check
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

            except TimeoutError:
                item.status = PypiStatusTypes.FETCH_TIMEOUT
            except NotFoundException:
                item.status = PypiStatusTypes.NOT_FOUND
            except ClientConnectionError:
                item.status = PypiStatusTypes.CONNECT_ERROR
                LOGGER.exception("Client connect error")

        if save_settings:
            await self.settings.async_write_settings()

        if self.session and self.close_session:
            await self.session.close()

    # ------------------------------------------------------------------
    async def async_get_package_version(self, package: str) -> str:
        """Pypi package version."""
        # https://pypi.org/pypi/pypiserver/json
        # https://pypi.org/project/pypiserver/

        json_dict: dict = {}

        async with timeout(5):
            response = await self.session.request(
                "GET", "https://pypi.org/pypi/" + package + "/json"
            )
            json_dict = orjson.loads(await response.text())

        if "message" in json_dict and json_dict["message"] == "Not Found":
            raise NotFoundException

        return json_dict["info"]["version"]


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class NotFoundException(Exception):
    """Not found exception."""


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class FindPyPiPackage:
    """Find Pypi package interface."""

    # ------------------------------------------------------------------
    async def async_exist(self, session: ClientSession | None, package: str) -> bool:
        """Pypi package exist."""
        close_session: bool = False
        ret_val: bool = True
        json_dict: dict = {}

        if session is None:
            session = ClientSession()
            close_session = True

        try:
            async with timeout(5):
                response = await session.request(
                    "GET", "https://pypi.org/pypi/" + package + "/json"
                )
                json_dict = orjson.loads(await response.text())

        except TimeoutError:
            ret_val = False

        if "message" in json_dict and json_dict["message"] == "Not Found":
            ret_val = False
        # https://pypi.org/pypi/pypiserver/json
        # https://pypi.org/project/pypiserver/
        # return json_dict["info"]["version"]

        if session and close_session:
            await session.close()

        return ret_val
