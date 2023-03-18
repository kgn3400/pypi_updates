"""Config flow for Pypi updates integration."""
from __future__ import annotations

from typing import Any
import voluptuous as vol
from homeassistant.helpers.aiohttp_client import async_get_clientsession

#  from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)
from .component_api import FindPyPiPackage

from .const import (
    CONF_HOURS_BETWEEN_CHECK,
    CONF_ADD_MORE,
    CONF_CLEAR_UPDATES_AFTER_HOURS,
    CONF_PYPI_ITEM,
    CONF_PYPI_LIST,
    DOMAIN,
    DOMAIN_NAME,
    LOGGER,
)


# ------------------------------------------------------------------
async def _validate_input(
    hass: HomeAssistant, user_input: dict[str, Any], errors: dict[str, str]
) -> bool:
    """Validate the user input allows us to connect."""

    if CONF_PYPI_ITEM not in user_input:
        user_input[CONF_PYPI_ITEM] = ""

    if (
        user_input[CONF_PYPI_ITEM].strip() != ""
        and await FindPyPiPackage().exist(
            async_get_clientsession(hass), user_input[CONF_PYPI_ITEM].strip()
        )
        is False
    ):
        errors["base"] = "missing_pypi_package"
        return False

    return True


# ------------------------------------------------------------------
def _create_form(
    user_input: dict[str, Any] | None = None,
) -> vol.Schema:
    """Create a form for step/option."""

    if user_input is None:
        user_input = {}
        user_input[CONF_PYPI_LIST] = []

    return vol.Schema(
        {
            vol.Optional(
                CONF_PYPI_LIST,
                default=user_input.get(CONF_PYPI_LIST, []),
            ): cv.multi_select(user_input.get(CONF_PYPI_LIST, [])),
            vol.Optional(
                CONF_PYPI_ITEM,
                default=user_input.get(CONF_PYPI_ITEM, ""),
            ): str,
            vol.Required(
                CONF_HOURS_BETWEEN_CHECK,
                default=user_input.get(CONF_HOURS_BETWEEN_CHECK, 12),
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
                default=user_input.get(CONF_CLEAR_UPDATES_AFTER_HOURS, 24),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=696,
                    mode=NumberSelectorMode.BOX,
                    unit_of_measurement="hours",
                )
            ),
            vol.Required(
                CONF_ADD_MORE,
                default=user_input.get(CONF_ADD_MORE, True),
            ): cv.boolean,
        }
    )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class ConfigFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HiperDrift"""

    VERSION = 1

    # ------------------------------------------------------------------
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    if user_input[CONF_PYPI_ITEM].strip() != "":
                        user_input[CONF_PYPI_LIST].append(
                            user_input.get(CONF_PYPI_ITEM)
                        )
                        user_input[CONF_PYPI_LIST].sort()
                        user_input[CONF_PYPI_ITEM] = ""

                    if user_input[CONF_ADD_MORE] is True:
                        return self.async_show_form(
                            step_id="user",
                            data_schema=_create_form(user_input),
                            errors=errors,
                        )

                    return self.async_create_entry(
                        title=DOMAIN_NAME, data=user_input, options=user_input
                    )

            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        # else:
        #     user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=_create_form(user_input),
            errors=errors,
        )

    # ------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Get the options flow."""
        return OptionsFlowHandler(config_entry)


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class OptionsFlowHandler(OptionsFlow):
    """Options flow for Pypi updates"""

    def __init__(
        self,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize options flow."""

        self.config_entry = config_entry

        self._selection: dict[str, Any] = {}
        # self._configs: dict[str, Any] = self.config_entry.data.copy()
        self._options: dict[str, Any] = self.config_entry.options.copy()

    # ------------------------------------------------------------------
    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                if await _validate_input(self.hass, user_input, errors):
                    if user_input[CONF_PYPI_ITEM].strip() != "":
                        user_input[CONF_PYPI_LIST].append(
                            user_input.get(CONF_PYPI_ITEM)
                        )
                        user_input[CONF_PYPI_LIST].sort()
                        user_input[CONF_PYPI_ITEM] = ""

                    if user_input[CONF_ADD_MORE] is True:
                        return self.async_show_form(
                            step_id="init",
                            data_schema=_create_form(user_input),
                            errors=errors,
                        )

                    return self.async_create_entry(title=DOMAIN_NAME, data=user_input)
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        else:
            user_input = self._options.copy()
            user_input[CONF_ADD_MORE] = True

        return self.async_show_form(
            step_id="init",
            data_schema=_create_form(user_input),
            errors=errors,
        )


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class MissingSelection(HomeAssistantError):
    """Error to indicate nothing was selected."""


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class MissingCity(HomeAssistantError):
    """Error to indicate nothing was selected."""


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class MissingStreet(HomeAssistantError):
    """Error to indicate nothing was selected."""
