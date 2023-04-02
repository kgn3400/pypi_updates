"""Settings handling."""
# pylintx: disable=unspecified-encoding, attribute-defined-outside-init

from os import mkdir, path, remove, sep

import jsonpickle

# from homeassistant.helpers.storage import STORAGE_DIR
#       hass.config.path(STORAGE_DIR, "vicare_token.save"),


# ------------------------------------------------------------------
class SettingsJson:
    """Settings class."""

    _REL_PATH: str = "userfiles"
    _SETTING_FILENAME: str = "settings.json"

    def __init__(self) -> None:
        """Init."""
        self._settings_file: str = ""

        self._write_underscore_attributes: bool = False

    # ------------------------------------------------------------------
    def set_settings_file_name(self, settings_file: str = "") -> None:
        """set_settings_file_name."""

        if settings_file == "":
            self._settings_file = (
                path.dirname(__file__)
                + sep
                + self._REL_PATH
                + sep
                + self._SETTING_FILENAME
            )
        else:
            self._settings_file = settings_file

    # ------------------------------------------------------------------
    def read_settings(self, settings_file: str = "") -> None:
        """read_settings."""
        if hasattr(self, "__dict__") is False:
            return

        self.set_settings_file_name(settings_file)

        try:
            with open(self._settings_file, encoding="UTF-8") as settingsfile:
                tmp_obj = jsonpickle.decode(settingsfile.read())

                if hasattr(tmp_obj, "__dict__") is False:
                    return

                self.__dict__.update(tmp_obj.__dict__)

        except FileNotFoundError:
            pass

    # ------------------------------------------------------------------
    def __getstate__(self) -> dict:
        """Get state."""
        tmp_dict = self.__dict__.copy()
        del tmp_dict["_write_underscore_attributes"]
        del tmp_dict["_settings_file"]

        if self._write_underscore_attributes is False:

            def remove_underscore_attrib(obj) -> None:
                for key in list(obj):
                    if hasattr(obj[key], "__dict__"):
                        tmp = obj[key]
                        remove_underscore_attrib(tmp.__dict__)

                    if key[0:1] == "_":
                        del obj[key]

            remove_underscore_attrib(tmp_dict)
        return tmp_dict

    # ------------------------------------------------------------------
    def write_settings(
        self, unpicklable: bool = True, write_underscore_attributes: bool = False
    ) -> None:
        """Write settings."""

        if path.exists(path.dirname(self._settings_file)) is not True:
            mkdir(path.dirname(self._settings_file))

        self._write_underscore_attributes = write_underscore_attributes
        jsonpickle.set_encoder_options("json", ensure_ascii=False)

        with open(self._settings_file, "w", encoding="UTF-8") as settingsfile:
            settingsfile.write(
                jsonpickle.encode(self, unpicklable=unpicklable, indent=4)  # type: ignore
            )

    # ------------------------------------------------------------------
    def delete_settings(self, settings_file: str = "") -> bool:
        """Delete settings."""
        if self._settings_file == "" or settings_file != "":
            self.set_settings_file_name(settings_file)

        if path.exists("demofile.txt"):
            try:
                remove("demofile.txt")
            except FileNotFoundError:
                return False
            return True
        else:
            return False
