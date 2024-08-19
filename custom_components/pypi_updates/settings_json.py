"""Settings handling."""
# pylintx: disable=unspecified-encoding, attribute-defined-outside-init

from os import mkdir, path, remove, sep

import aiofiles
import jsonpickle

#       hass.config.path(STORAGE_DIR, "vicare_token.save"),


# ------------------------------------------------------------------
class SettingsJson:
    """Settings class."""

    _REL_PATH: str = "userfiles"
    _SETTING_FILENAME: str = "settings.json"

    def __init__(self) -> None:
        """Init."""
        self.settings_file___: str = ""

        self.write_hidden_attributes___: bool = False

    # ------------------------------------------------------------------
    def set_settings_file_name(self, settings_file: str = "") -> None:
        """set_settings_file_name."""

        if settings_file == "":
            self.settings_file___ = (
                path.dirname(__file__)
                + sep
                + self._REL_PATH
                + sep
                + self._SETTING_FILENAME
            )
        else:
            self.settings_file___ = settings_file

    # ------------------------------------------------------------------
    async def async_read_settings(self, settings_file: str = "") -> None:
        """read_settings."""
        if hasattr(self, "__dict__") is False:
            return

        self.set_settings_file_name(settings_file)

        try:
            async with aiofiles.open(
                self.settings_file___, encoding="UTF-8"
            ) as settingsfile:
                tmp_obj = jsonpickle.decode(await settingsfile.read())

                if hasattr(tmp_obj, "__dict__") is False:
                    return

                self.__dict__.update(tmp_obj.__dict__)

        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    def __getstate__(self) -> dict:
        """Get state."""
        tmp_dict = self.__dict__.copy()
        del tmp_dict["write_hidden_attributes___"]
        del tmp_dict["settings_file___"]

        if self.write_hidden_attributes___ is False:
            try:

                def remove_hidden_attrib(obj) -> None:
                    for key in list(obj):
                        if len(key) > 2 and key[0:2] == "__":
                            continue
                        elif hasattr(obj[key], "__dict__"):
                            remove_hidden_attrib(obj[key].__dict__)

                        # Remove hidden attributes
                        elif len(key) > 3 and key[-3:] == "___":
                            del obj[key]

                        elif isinstance(obj[key], list):
                            for item in obj[key]:
                                if hasattr(item, "__dict__"):
                                    remove_hidden_attrib(item.__dict__)

                remove_hidden_attrib(tmp_dict)
            except Exception:  # pylint: disable=broad-except
                pass
        return tmp_dict

    # ------------------------------------------------------------------
    async def async_write_settings(
        self, unpicklable: bool = True, write_hidden_attributes: bool = False
    ) -> None:
        """Write settings."""

        if path.exists(path.dirname(self.settings_file___)) is not True:
            mkdir(path.dirname(self.settings_file___))

        self.write_hidden_attributes___ = write_hidden_attributes
        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        async with aiofiles.open(
            self.settings_file___, "w", encoding="UTF-8"
        ) as settingsfile:
            await settingsfile.write(
                jsonpickle.encode(self, unpicklable=unpicklable, indent=4)
            )

    # ------------------------------------------------------------------
    def get_data(self, unpicklable: bool = True):
        """Get data."""
        return jsonpickle.encode(self, unpicklable=unpicklable, indent=4)

    # ------------------------------------------------------------------
    def delete_settings(self, settings_file: str = "") -> bool:
        """Delete settings."""
        if self.settings_file___ == "" or settings_file != "":
            self.set_settings_file_name(settings_file)

        if path.exists("demofile.txt"):
            try:
                remove("demofile.txt")
            except FileNotFoundError:
                return False
            return True

        return False
