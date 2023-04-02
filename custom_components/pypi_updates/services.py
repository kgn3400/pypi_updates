"""Services for Pypi updates integration."""
from homeassistant.core import HomeAssistant

from .component_api import ComponentApi
from .const import DOMAIN


async def async_setup_services(
    hass: HomeAssistant, component_api: ComponentApi
) -> None:
    """Set up the services for the Pypi updates integration."""

    hass.services.async_register(DOMAIN, "update", component_api.async_update_service)
    hass.services.async_register(DOMAIN, "reset", component_api.async_reset_service)
