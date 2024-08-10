"""The Pypi updates integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

# from homeassistant.helpers.device_registry import DeviceEntry
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
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pypi updates from a config entry."""
    session = async_get_clientsession(hass)
    hass.data.setdefault(DOMAIN, {})

    component_api: ComponentApi = ComponentApi(
        hass,
        entry,
        session,
        entry.options[CONF_PYPI_LIST],
        entry.options[CONF_HOURS_BETWEEN_CHECK],
        entry.options[CONF_CLEAR_UPDATES_AFTER_HOURS],
    )

    coordinator: DataUpdateCoordinator = DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
        update_interval=timedelta(minutes=5),
        update_method=component_api.async_update,
    )

    component_api.coordinator = coordinator

    # await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(update_listener))

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "component_api": component_api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# ------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


# ------------------------------------------------------------------
async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


# ------------------------------------------------------------------
async def update_listener(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> None:
    """Reload on config entry update."""

    component_api: ComponentApi = hass.data[DOMAIN][config_entry.entry_id][
        "component_api"
    ]

    await hass.config_entries.async_reload(config_entry.entry_id)
    await component_api.async_update()
