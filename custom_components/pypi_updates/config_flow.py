"""Config flow for Pypi updates integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast

from aiohttp import ClientConnectionError
import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.util.uuid import random_uuid_hex

from .component_api import FindPyPiPackage, NotFoundException
from .const import (
    CONF_CLEAR_UPDATES_AFTER_HOURS,
    CONF_DEFAULT_MD_HEADER_TEMPLATE,
    CONF_DEFAULT_MD_ITEM_TEMPLATE,
    CONF_DEFAULT_MD_NO_UPDATES_TEMPLATE,
    CONF_HOURS_BETWEEN_CHECK,
    CONF_MD_HEADER_TEMPLATE,
    CONF_MD_ITEM_TEMPLATE,
    CONF_MD_NO_UPDATES_TEMPLATE,
    CONF_PYPI_ITEM,
    CONF_PYPI_LIST,
    DOMAIN,
    DOMAIN_NAME,
)
from .hass_util import Translate

tmp_item_list: list[str] = []


# ------------------------------------------------------------------
async def _validate_input(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate the user input."""

    if CONF_PYPI_ITEM not in user_input:
        user_input[CONF_PYPI_ITEM] = ""
        return user_input

    try:
        if (
            user_input[CONF_PYPI_ITEM].strip() != ""
            and await FindPyPiPackage().async_get_package_version(
                async_get_clientsession(handler.parent_handler.hass),
                user_input[CONF_PYPI_ITEM].strip(),
            )
            == ""
        ):
            raise SchemaFlowError("missing_pypi_package")
    except (TimeoutError, NotFoundException, ClientConnectionError):
        raise SchemaFlowError("missing_pypi_package") from None

    user_input[CONF_PYPI_LIST].append(user_input.get(CONF_PYPI_ITEM))
    user_input[CONF_PYPI_LIST].sort()

    return user_input


# ------------------------------------------------------------------
async def choose_config_step(options: dict[str, Any]) -> str | None:
    """Return next step_id for config flow."""

    if options[CONF_PYPI_ITEM].strip() != "":
        options[CONF_PYPI_ITEM] = ""
        return "user"

    return None


# ------------------------------------------------------------------
async def choose_options_step(options: dict[str, Any]) -> str | None:
    """Return next step_id for options flow."""

    if options[CONF_PYPI_ITEM].strip() != "":
        options[CONF_PYPI_ITEM] = ""
        return "init"

    return None


# ------------------------------------------------------------------
async def create_schema(handler: SchemaCommonFlowHandler) -> vol.Schema:
    """Return schema for the config/options step."""

    options: dict[str, Any] = handler.options.copy()

    return vol.Schema(
        {
            vol.Optional(
                CONF_PYPI_ITEM,
            ): str,
            vol.Optional(
                CONF_PYPI_LIST,
                default=[],
            ): cv.multi_select(options.get(CONF_PYPI_LIST, [])),
            vol.Optional(
                CONF_MD_HEADER_TEMPLATE,
                default=await Translate(
                    handler.parent_handler.hass
                ).async_get_localized_str(
                    CONF_DEFAULT_MD_HEADER_TEMPLATE,
                    file_name="_defaults.json",
                ),
            ): TextSelector(
                TextSelectorConfig(multiline=True, type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_MD_ITEM_TEMPLATE,
                default=await Translate(
                    handler.parent_handler.hass
                ).async_get_localized_str(
                    CONF_DEFAULT_MD_ITEM_TEMPLATE, file_name="_defaults.json"
                ),
            ): TextSelector(
                TextSelectorConfig(multiline=True, type=TextSelectorType.TEXT)
            ),
            vol.Optional(
                CONF_MD_NO_UPDATES_TEMPLATE,
                default=await Translate(
                    handler.parent_handler.hass
                ).async_get_localized_str(
                    CONF_DEFAULT_MD_NO_UPDATES_TEMPLATE, file_name="_defaults.json"
                ),
            ): TextSelector(
                TextSelectorConfig(multiline=True, type=TextSelectorType.TEXT)
            ),
            vol.Required(
                CONF_HOURS_BETWEEN_CHECK,
                default=12,
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=696,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="hours",
                )
            ),
            vol.Required(
                CONF_CLEAR_UPDATES_AFTER_HOURS,
                default=24,
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=696,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="hours",
                )
            ),
        }
    )


# ------------------------------------------------------------------
async def config_schema_handler(
    handler: SchemaCommonFlowHandler,
) -> vol.Schema:
    """Return schema for the sensor config step."""

    if handler.parent_handler.unique_id is None:
        await handler.parent_handler.async_set_unique_id(random_uuid_hex())
        handler.parent_handler._abort_if_unique_id_configured()  # noqa: SLF001

    return await create_schema(handler)


CONFIG_FLOW = {
    "user": SchemaFlowFormStep(
        create_schema,
        validate_user_input=_validate_input,
        next_step=choose_config_step,
    ),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(
        create_schema,
        validate_user_input=_validate_input,
        next_step=choose_options_step,
    ),
}


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return config entry title."""

        return cast(str, DOMAIN_NAME)

    # ------------------------------------------------------------------
    @callback
    def async_config_flow_finished(self, options: Mapping[str, Any]) -> None:
        """Take necessary actions after the config flow is finished, if needed.

        The options parameter contains config entry options, which is the union of user
        input from the config flow steps.
        """
        # del options[CONF_ADD_MORE]

    @callback
    @staticmethod
    def async_options_flow_finished(
        hass: HomeAssistant, options: Mapping[str, Any]
    ) -> None:
        """Take necessary actions after the options flow is finished, if needed.

        The options parameter contains config entry options, which is the union of
        stored options and user input from the options flow steps.
        """
        # del options[CONF_ADD_MORE]
