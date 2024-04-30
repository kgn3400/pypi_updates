
# PyPi updates

![GitHub release (latest by date)](https://img.shields.io/github/v/release/kgn3400/pypi_updates)
![GitHub all releases](https://img.shields.io/github/downloads/kgn3400/pypi_updates/total)
![GitHub last commit](https://img.shields.io/github/last-commit/kgn3400/pypi_updates)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/kgn3400/pypi_updates)
[![Validate% with hassfest](https://github.com/kgn3400/pypi_updates/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/kgn3400/pypi_updates/blob/main/.github/workflows/hassfest-validate.yaml)

The PyPi updates integration allows you to monitor a list of PyPi package and get notified when a updates is available.
For installation instructions until the State updated helper is part of HACS, [see this guide](https://hacs.xyz/docs/faq/custom_repositories).

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pypi_updates)

## Configuration

Configuration is setup via UI in Home assistant. To add one, go to [Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations) and click the add button. Next choose the [PyPi updates](https://my.home-assistant.io/redirect/config_flow_start?domain=pypi_updates) option.

<img src="https://github.com/kgn3400/pypi_updates/blob/main/images/config.png" width="500" height="auto" alt="Config">
<br/>


| Field name | Mandatory/Optional | Description |
|------------|------------------|-------------|
| Name | Optional | Name. If empty, entity id name are used  |
| Entity id | Mandatory | Entity that this sensor tracks  |
| Attribute | Optional | Attribute of entity that this sensor tracks  |
| Icon | Mandatory | Icon used by entity  |
| Clear updates after | Mandatory | User defined time period indicating when to clear the entity  |
| Text template | Optional | Defines a template to create the text state attribute. Value = new_value, old_value, entity_id, attribute and last_updated |

## Exposed state attributes

The state updated helper integration provides the following state attributes.

| Attribute | Description |
|-----------|-------------|
| new_value  | New state/state_attribute value |
| old_value  | Old state/state_attribute value |
| text  | Text generated from template |
| last_updated  | Last time the state/state_attribute was updated |

## Services

Available services: __reset__ and __reset_all__.

### Service state_updated.reset

Reset a specific State Updated entity.

|Service data attribute | Optional | Description|
|-----------------------|----------|------------|
|entity_id | No | Name of the State updated entity to take reset.|

### Service state_updated.reset_all

Reset all State updated entities.

