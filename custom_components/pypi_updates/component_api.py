"""Component api."""

from asyncio import timeout
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from aiohttp.client import ClientConnectionError, ClientSession
import orjson

from homeassistant.config_entries import ConfigEntry

# from homeassistant.const import STATE_OFF
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import issue_registry as ir
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
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        session: ClientSession | None,
        entry_pypi_list: list[str],
        hours_between_updates: int,
        clear_updates_after_hours: int,
    ) -> None:
        """Component api."""

        self.hass = hass
        self.coordinator: DataUpdateCoordinator = coordinator
        self.entry: ConfigEntry = entry
        self.session: ClientSession | None = session
        self.entry_pypi_list: list[str] = entry_pypi_list
        self.hours_between_updates: int = hours_between_updates
        self.clear_updates_after_hours: int = clear_updates_after_hours

        self.entity_id: str = ""
        self.close_session: bool = False
        self.updates: bool = False
        # self.pypi_updates: list[PyPiBaseItem] = []
        self.last_pypi_update: PyPiBaseItem = PyPiBaseItem()
        self.markdown: str = ""
        self.last_full_update: datetime = datetime.now()
        self.last_error_template: str = ""
        self.last_error_txt_template: str = ""

        self.settings: PyPiSettings = PyPiSettings(hass)

        """Set up the actions for the Pypi updates integration."""
        hass.services.async_register(DOMAIN, "update", self.async_update_service)
        hass.services.async_register(DOMAIN, "reset", self.async_reset_service)

    # ------------------------------------------------------------------
    async def async_sync_lists(self) -> None:
        """Sync lists."""

        save_settings: bool = False

        def sort_key(item: PyPiItem) -> str:
            return item.package_name

        # Delete part
        for index, item in reversed(list(enumerate(self.settings.pypi_list))):
            if item.package_name not in self.entry_pypi_list:
                save_settings = True
                del self.settings.pypi_list[index]

        # Add new items
        cur_package: list = [itemx.package_name for itemx in self.settings.pypi_list]

        for itemy in self.entry_pypi_list:
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
        self.updates = False
        self.last_pypi_update = PyPiBaseItem()

        await self.async_create_markdown()
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_update_service(self, call: ServiceCall) -> None:
        """Pypi updates service."""

        await self.async_go_update(True)
        await self.coordinator.async_refresh()

    # ------------------------------------------------------------------
    async def async_setup(self) -> None:
        """Set up the Pypi updates component."""

        await self.settings.async_read_settings()

        await self.async_sync_lists()
        self.check_list_for_updates()
        await self.async_create_markdown()

    # ------------------------------------------------------------------
    async def async_update(self) -> None:
        """Update."""

        await self.async_go_update()

    # ------------------------------------------------------------------
    async def async_go_update(self, force_update: bool = False) -> None:
        """Go updates."""

        if (
            force_update
            or (self.last_full_update + timedelta(hours=self.hours_between_updates))
            < datetime.now()
        ):
            if await self.async_check_pypi_for_update():
                await self.async_create_markdown()

            self.last_full_update = datetime.now()

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

                for item in self.settings.pypi_list:
                    if item.status == PypiStatusTypes.UPDATED:
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
    async def async_check_pypi_for_update(self) -> bool:
        """Check pypi updates."""

        save_settings: bool = False
        self.last_pypi_update = PyPiBaseItem()

        if self.session is None:
            self.session = ClientSession()
            self.close_session = True

        find_pypi_package: FindPyPiPackage = FindPyPiPackage()

        for item in self.settings.pypi_list:
            try:
                version = await find_pypi_package.async_get_package_version(
                    self.session, item.package_name
                )

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

                    self.last_pypi_update = PyPiBaseItem(
                        item.package_name,
                        item.version,
                        item.old_version,
                    )

                elif (
                    item.status == PypiStatusTypes.UPDATED
                    and (
                        item.last_update
                        + timedelta(hours=self.clear_updates_after_hours)
                    )
                    < datetime.now()
                ):
                    save_settings = True
                    item.status = PypiStatusTypes.OK

            except TimeoutError:
                item.status = PypiStatusTypes.FETCH_TIMEOUT
            except NotFoundException:
                item.status = PypiStatusTypes.NOT_FOUND
            except ClientConnectionError:
                item.status = PypiStatusTypes.CONNECT_ERROR
                LOGGER.exception("Client connect error")

        self.check_list_for_updates()

        if save_settings:
            await self.settings.async_write_settings()

        if self.session and self.close_session:
            await self.session.close()

        return save_settings

    # ------------------------------------------------------------------
    def check_list_for_updates(self) -> bool:
        """Check list for updates."""

        for item in self.settings.pypi_list:
            if item.status == PypiStatusTypes.UPDATED:
                self.updates = True
                return True

        self.updates = False

        return False


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class NotFoundException(Exception):
    """Not found exception."""


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class FindPyPiPackage:
    """Find Pypi package interface."""

    # ------------------------------------------------------------------
    async def async_get_package_version(
        self, session: ClientSession | None, package: str
    ) -> str:
        """Pypi package exist."""
        close_session: bool = False

        if session is None:
            session = ClientSession()
            close_session = True

        """Pypi package version."""
        # https://pypi.org/pypi/pypiserver/json
        # https://pypi.org/project/pypiserver/

        json_dict: dict = {}

        async with timeout(5):
            response = await session.get("https://pypi.org/pypi/" + package + "/json")
            json_dict = orjson.loads(await response.text())

        if "message" in json_dict and json_dict["message"] == "Not Found":
            raise NotFoundException

        if session and close_session:
            await session.close()

        return json_dict["info"]["version"]
