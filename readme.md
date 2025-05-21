<!-- markdownlint-disable MD041 -->
![GitHub release (latest by date)](https://img.shields.io/github/v/release/kgn3400/pypi_updates)
![GitHub all releases](https://img.shields.io/github/downloads/kgn3400/pypi_updates/total)
![GitHub last commit](https://img.shields.io/github/last-commit/kgn3400/pypi_updates)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/kgn3400/pypi_updates)
[![Validate% with hassfest](https://github.com/kgn3400/pypi_updates/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/kgn3400/pypi_updates/actions/workflows/hassfest-validate.yaml)

<img align="left" width="80" height="80" src="https://kgn3400.github.io/pypi_updates/assets/icon.png" alt="App icon">

# PyPi updates

<br/>
The PyPi updates integration allows you to monitor a list of PyPi package and get notified when a updates is available.

## Installation

For installation search for Pypi updates in HACS and download.
Or click
[![My Home Assistant](https://img.shields.io/badge/Home%20Assistant-%2341BDF5.svg?style=flat&logo=home-assistant&label=Add%20to%20HACS)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kgn3400&repository=pypi_updates&category=integration) to add the repository to HACS.

Then click to
[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=pypi_updates)

## Configuration

Configuration is setup via UI in Home assistant. To add one, go to [Settings > Devices & Services](https://my.home-assistant.io/redirect/integrations) and click the add button. Next choose the [PyPi updates](https://my.home-assistant.io/redirect/config_flow_start?domain=pypi_updates) option.

<!-- <img src="images/config.png" width="500" height="auto" alt="Config"> -->
<img src="https://kgn3400.github.io/pypi_updates/assets/config.png" width="500" height="auto" alt="Config">
<br/>

## Exposed state attributes

The PyPi updates integration provides the following state attributes.

| Attribute     | Description                                                                      |
|---------------|----------------------------------------------------------------------------------|
| pypi_updates  | List of package which have been updated                                          |
| Markdown      | Pre formatted markdown text with updated package information and link to package |

Using the markdown card with the content of the markdown attribute:

<!-- <img src="images/updates_markdown.png" width="500" height="auto" alt="updates_markdown"> -->
<img src="https://kgn3400.github.io/pypi_updates/assets/updates_markdown.png" width="500" height="auto" alt="updates_markdown">
<br/>

## Actions

Available actions: __Reset PyPi updates__ and __Check PyPi__.

### Action pypi_updates.reset_pypi_updates

Reset notification about new updates.

### Action pypi_updates.check_pypi

CHeck for new updates.
