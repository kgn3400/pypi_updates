"""Constants for Pypi updates integration."""
from logging import Logger, getLogger

DOMAIN = "pypi_updates"
DOMAIN_NAME = "PyPi updates"
LOGGER: Logger = getLogger(__name__)

CONF_PYPI_LIST: str = "pypi_list"
CONF_PYPI_ITEM: str = "pypi_item"
CONF_HOURS_BETWEEN_CHECK: str = "hours_between_check"
CONF_CLEAR_UPDATES_AFTER_HOURS: str = "clear_update_after_hours"

CONF_ADD_MORE: str = "add_more"
