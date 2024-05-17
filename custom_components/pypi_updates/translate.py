"""Hmmm."""

import json
import os
import os.path
from typing import Any

from homeassistant.components.frontend import storage as frontend_store
from homeassistant.core import HomeAssistant


# ------------------------------------------------------------------
# ------------------------------------------------------------------
class Translate:
    """Translate."""

    __language: str = ""
    __json_dict: dict[str, Any] = {}

    def __init__(self, hass: HomeAssistant) -> None:
        """Init."""
        self.hass = hass

    # ------------------------------------------------------------------
    async def async_get_localized_str(
        self,
        key: str,
        language: str | None = None,
        file_name: str = ".json",
        load_only: str = "",
        default: Any = "",
        **kvargs,
    ) -> str:
        """Get localized string."""

        if language is None:
            language = self.hass.config.language

            owner = await self.hass.auth.async_get_owner()

            if owner is not None:
                _, owner_data = await frontend_store.async_user_store(
                    self.hass, owner.id
                )

                if "language" in owner_data and "language" in owner_data["language"]:
                    language = owner_data["language"]["language"]

        self.__check_language_loaded(
            str(language), file_name=file_name, load_only=load_only
        )

        if len(kvargs) == 0:
            return Translate.__json_dict.get(key, default)

        return str(Translate.__json_dict.get(key, default)).format(**kvargs)

    # ------------------------------------------------------------------
    def __check_language_loaded(
        self, language: str, file_name: str = ".json", load_only: str = ""
    ) -> None:
        """Check language."""

        # ------------------------------------------------------------------
        def recursive_flatten(
            prefix: Any, data: dict[str, Any], load_only: str = ""
        ) -> dict[str, Any]:
            """Return a flattened representation of dict data."""
            output = {}
            for key, value in data.items():
                if isinstance(value, dict):
                    output.update(
                        recursive_flatten(f"{prefix}{key}.", value, load_only)
                    )
                elif (
                    load_only != "" and f"{prefix}{key}".find(load_only) == 0
                ) or load_only == "":
                    output[f"{prefix}{key}"] = value
            return output

        if Translate.__language != language:
            Translate.__language = language

            filename = os.path.join(
                os.path.dirname(__file__), "translations", language + file_name
            )

            if os.path.isfile(filename):
                with open(filename) as json_file:
                    parsed_json = json.load(json_file)

                Translate.__json_dict = recursive_flatten("", parsed_json, load_only)
                return

            filename = os.path.join(
                os.path.dirname(__file__), "translations", "en" + file_name
            )

            if os.path.isfile(filename):
                with open(filename) as json_file:
                    parsed_json = json.load(json_file)

                Translate.__json_dict = recursive_flatten("", parsed_json, load_only)

                return
