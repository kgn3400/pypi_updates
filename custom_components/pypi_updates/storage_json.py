"""Settings handling."""

# import aiofiles
import jsonpickle

from homeassistant.core import HomeAssistant

from .const import STORAGE_KEY, STORAGE_VERSION
from .store_settings import StoreSettings


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class SettingsJson:
    """Settings class."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""

        self.write_hidden_attributes___: bool = False
        self.hass___ = hass
        self.store___ = StoreSettings(self.hass___, STORAGE_VERSION, STORAGE_KEY)

    # ------------------------------------------------------------------
    async def async_read_settings(self) -> None:
        """read_settings."""
        if hasattr(self, "__dict__") is False:
            return

        data = await self.store___.async_load()

        if data is None:
            return
        tmp_obj = jsonpickle.decode(data)

        if hasattr(tmp_obj, "__dict__") is False:
            return

        self.__dict__.update(tmp_obj.__dict__)

    # ------------------------------------------------------------------
    def __getstate__(self) -> dict:
        """Get state."""
        tmp_dict = self.__dict__.copy()
        del tmp_dict["write_hidden_attributes___"]
        del tmp_dict["hass___"]
        del tmp_dict["store___"]

        if self.write_hidden_attributes___ is False:
            try:

                def remove_hidden_attrib(obj) -> None:
                    for key in list(obj):
                        if len(key) > 2 and key[0:2] == "__":
                            continue
                        elif hasattr(obj[key], "__dict__"):  # noqa: RET507
                            remove_hidden_attrib(obj[key].__dict__)

                        # Remove hidden attributes
                        elif len(key) > 3 and key[-3:] == "___":
                            del obj[key]

                        elif isinstance(obj[key], list):
                            for item in obj[key]:
                                if hasattr(item, "__dict__"):
                                    remove_hidden_attrib(item.__dict__)

                remove_hidden_attrib(tmp_dict)
            except Exception:  # noqa: BLE001
                pass
        return tmp_dict

    # ------------------------------------------------------------------
    async def async_write_settings(
        self,
        unpicklable: bool = True,
        write_hidden_attributes: bool = False,
    ) -> None:
        """Write settings."""

        self.write_hidden_attributes___ = write_hidden_attributes
        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        await self.store___.async_save(jsonpickle.encode(self, unpicklable=unpicklable))

    # ------------------------------------------------------------------
    async def async_remove_settings(self) -> None:
        """Remove settings."""
        await self.store___.async_remove()
