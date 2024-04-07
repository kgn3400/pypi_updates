"""Constants for Pypi updates integration."""

from logging import Logger, getLogger

DOMAIN = "pypi_updates"
DOMAIN_NAME = "PyPi updates"
LOGGER: Logger = getLogger(__name__)

CONF_PYPI_LIST = "pypi_list"
CONF_PYPI_ITEM = "pypi_item"
CONF_HOURS_BETWEEN_CHECK = "hours_between_check"
CONF_CLEAR_UPDATES_AFTER_HOURS = "clear_update_after_hours"

CONF_MD_HEADER_TEMPLATE = "md_header_template"
CONF_DEFAULT_MD_HEADER_TEMPLATE = "config.step.user.data.default_md_header_template"

CONF_MD_ITEM_TEMPLATE = "md_item_template"
CONF_DEFAULT_MD_ITEM_TEMPLATE = "config.step.user.data.default_md_item_template"

CONF_MD_NO_UPDATES_TEMPLATE = "md_no_updates_template"
CONF_DEFAULT_MD_NO_UPDATES_TEMPLATE = (
    "config.step.user.data.default_md_no_updates_template"
)

CONF_LOAD_ONLY = "config.step.user.data.default"

CONF_ADD_MORE = "add_more"
