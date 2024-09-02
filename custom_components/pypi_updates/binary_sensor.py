"""Support for Pypi updates."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .component_api import ComponentApi
from .const import (
    CONF_CLEAR_UPDATES_AFTER_HOURS,
    CONF_HOURS_BETWEEN_CHECK,
    CONF_PYPI_LIST,
    DOMAIN,
    TRANSLATION_KEY,
)
from .entity import ComponentEntity


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Pypi updates setup."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    # component_api: ComponentApi = hass.data[DOMAIN][entry.entry_id]["component_api"]

    sensors = []

    sensors.append(PypiUpdatesBinarySensor(hass, coordinator, entry))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class PypiUpdatesBinarySensor(ComponentEntity, BinarySensorEntity):
    """Sensor class for Pypi updates."""

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: DataUpdateCoordinator,
        entry: ConfigEntry,
        # component_api: ComponentApi,
    ) -> None:
        """Binary sensor."""

        super().__init__(coordinator, entry)

        # self.component_api = component_api
        self.component_api = ComponentApi(
            hass,
            entry,
            async_get_clientsession(hass),
            entry.options[CONF_PYPI_LIST],
            entry.options[CONF_HOURS_BETWEEN_CHECK],
            entry.options[CONF_CLEAR_UPDATES_AFTER_HOURS],
        )

        self.coordinator.update_method = self.component_api.async_update
        self.coordinator.update_interval = timedelta(minutes=10)
        # self.coordinator = coordinator

        self.translation_key = TRANSLATION_KEY

        self._name = "Updates"
        self._unique_id = "updates"

        self.coordinator.setup_method = self.component_api.async_setup

    # ------------------------------------------------------
    @property
    def name(self) -> str:
        """Name.

        Returns:
            str: Name of sensor

        """
        return self._name

    # ------------------------------------------------------
    # @property
    # def icon(self) -> str:
    #     """Icon.

    #     Returns:
    #         str: Icon name

    #     """
    #     return "mdi:package-variant"

    # ------------------------------------------------------
    @property
    def is_on(self) -> bool:
        """Get the state."""

        return self.component_api.updates

    # ------------------------------------------------------
    @property
    def extra_state_attributes(self) -> dict:
        """Extra state attributes."""

        return {
            "last_pypi_update_version": self.component_api.last_pypi_update.version,
            "last_pypi_update_old_version": self.component_api.last_pypi_update.old_version,
            "last_pypi_update_package_name": self.component_api.last_pypi_update.package_name,
            "last_pypi_update_package_url": f"https://pypi.org/project/{self.component_api.last_pypi_update.package_name}/"
            if self.component_api.last_pypi_update.package_name
            else "",
            "pypi_updates": self.component_api.pypi_updates,
            "markdown": self.component_api.markdown,
        }

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """
        return self._unique_id

    # ------------------------------------------------------
    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    # ------------------------------------------------------
    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    # ------------------------------------------------------
    async def async_update(self) -> None:
        """Update the entity. Only used by the generic entity update service."""
        await self.coordinator.async_request_refresh()

    # ------------------------------------------------------
    @callback
    async def _handle_device_registry_updated(
        self, event: Event[dr.EventDeviceRegistryUpdatedData]
    ) -> None:
        """Handle when device registry updated."""

        if event.data["action"] == "remove":
            await self.component_api.settings.async_remove_settings()
            # await StoreSettings(self.hass, STORAGE_VERSION, STORAGE_KEY).async_remove()

    # ------------------------------------------------------
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""

        await super().async_added_to_hass()

        self.component_api.entity_id = self.entity_id

        # self.update_method = self.component_api.async_update
        # self.coordinator.update_interval = timedelta(minutes=5)
        await self.coordinator.async_config_entry_first_refresh()

        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
        self.hass.bus.async_listen(
            dr.EVENT_DEVICE_REGISTRY_UPDATED,
            self._handle_device_registry_updated,
        )
