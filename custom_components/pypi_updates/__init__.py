"""The Pypi updates integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .component_api import ComponentApi
from .const import (
    CONF_CLEAR_UPDATES_AFTER_HOURS,
    CONF_HOURS_BETWEEN_CHECK,
    CONF_PYPI_LIST,
    DOMAIN,
    LOGGER,
)

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR]


# ------------------------------------------------------------------
# ------------------------------------------------------------------
@dataclass
class CommonData:
    """Common data."""

    coordinator: DataUpdateCoordinator
    component_api: ComponentApi


# The type alias needs to be suffixed with 'ConfigEntry'
type CommonConfigEntry = ConfigEntry[CommonData]


# ------------------------------------------------------------------
async def async_setup_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Set up Pypi updates from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
    )

    component_api = ComponentApi(
        hass,
        coordinator,
        entry,
        async_get_clientsession(hass),
        entry.options[CONF_PYPI_LIST],
        entry.options[CONF_HOURS_BETWEEN_CHECK],
        entry.options[CONF_CLEAR_UPDATES_AFTER_HOURS],
    )

    entry.runtime_data = CommonData(
        component_api=component_api,
        coordinator=coordinator,
    )

    entry.async_on_unload(entry.add_update_listener(update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: CommonConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
async def update_listener(
    hass: HomeAssistant,
    config_entry: CommonConfigEntry,
) -> None:
    """Reload on config entry update."""

    await hass.config_entries.async_reload(config_entry.entry_id)
