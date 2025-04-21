"""Support for Pypi updates."""

from __future__ import annotations

from datetime import timedelta

from custom_components.pypi_updates.pypi_settings import PyPiBaseItem, PypiStatusTypes
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import CommonConfigEntry
from .component_api import ComponentApi
from .entity import ComponentEntity


# ------------------------------------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    entry: CommonConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Entry for Pypi updates setup."""

    sensors = []

    sensors.append(PypiUpdatesBinarySensor(hass, entry))

    async_add_entities(sensors)


# ------------------------------------------------------
# ------------------------------------------------------
class PypiUpdatesBinarySensor(ComponentEntity, BinarySensorEntity):
    """Sensor class for Pypi updates."""

    # ------------------------------------------------------
    def __init__(
        self,
        hass: HomeAssistant,
        entry: CommonConfigEntry,
    ) -> None:
        """Binary sensor."""

        super().__init__(entry.runtime_data.coordinator, entry)

        self.component_api: ComponentApi = entry.runtime_data.component_api

        self.coordinator.update_method = self.component_api.async_update
        self.coordinator.update_interval = timedelta(minutes=10)
        self.entry: CommonConfigEntry = entry

        self.hass: HomeAssistant = hass
        self.translation_key = "updates"

        # self._name = "Pypi updates"
        # self._unique_id = "pypi_updates"

        self.coordinator.setup_method = self.component_api.async_setup

    # ------------------------------------------------------
    # @property
    # def name(self) -> str:
    #     """Name.

    #     Returns:
    #         str: Name of sensor

    #     """
    #     return self._name

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
            "updates": [
                PyPiBaseItem(x.package_name, x.version, x.old_version)
                for x in self.component_api.settings.pypi_list
                if x.status == PypiStatusTypes.UPDATED
            ],
            "markdown": self.component_api.markdown,
        }

    # ------------------------------------------------------
    @property
    def unique_id(self) -> str:
        """Unique id.

        Returns:
            str: Unique id

        """
        return self.entry.entry_id

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
