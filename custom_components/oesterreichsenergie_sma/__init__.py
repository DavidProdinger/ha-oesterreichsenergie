"""
The Österreichsenergie Smart-Meter-Adapter integration with Home Assistant.

For more details about this integration, please refer to
https://github.com/DavidProdinger/ha-oesterreichsenergie
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components import mqtt as mqtt_integration
from homeassistant.components.mqtt import CONF_QOS, CONF_TOPIC
from homeassistant.const import (
    CONF_HOST,
    CONF_OPTIONS,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
    Platform,
)
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import OeSmaApiClient
from .const import DOMAIN, LOGGER, OeSmaApiType
from .coordinator import (
    OeSmaMeasurementDataUpdateCoordinator,
    OeSmaStatusDataUpdateCoordinator,
)
from .data import OeSmaData
from .mqtt import OeSmaMqttMessageHandler
from .obis import get_meter_number

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import OeSmaConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: OeSmaConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    setup_return = False

    match entry.options.get("type"):
        case OeSmaApiType.JSON:
            setup_return = await _async_setup_json_entry(hass, entry)
        case OeSmaApiType.MQTT:
            setup_return = await _async_setup_mqtt_entry(hass, entry)
        case _:
            LOGGER.error("Unknown API type: %s", entry.options.get("type"))
            return False

    if setup_return:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return setup_return


async def _async_setup_json_entry(hass: HomeAssistant, entry: OeSmaConfigEntry) -> bool:
    """Set up this integration using JSON configuration."""
    measurement_coordinator = OeSmaMeasurementDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=15),
    )
    status_coordinator = OeSmaStatusDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )

    entry.runtime_data = OeSmaData(
        type=OeSmaApiType.JSON,
        json_client=OeSmaApiClient(
            host=entry.data[CONF_HOST],
            token=entry.data[CONF_TOKEN],
            session=async_get_clientsession(
                hass,
                # default to false due to the self-signed certificates
                verify_ssl=entry.data[CONF_OPTIONS][CONF_VERIFY_SSL] or False,
            ),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        json_measurement_coordinator=measurement_coordinator,
        json_status_coordinator=status_coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await measurement_coordinator.async_config_entry_first_refresh()
    await status_coordinator.async_config_entry_first_refresh()

    # create devices
    device_registry = dr.async_get(hass)
    # adapter
    adapter = status_coordinator.data
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        entry_type=dr.DeviceEntryType.SERVICE,
        connections={(dr.CONNECTION_NETWORK_MAC, adapter["wifi"]["mac"])},
        identifiers={(entry.domain, f"{entry.entry_id}-sma")},
        translation_key="sma",
        model=adapter["sma_module_type"],
        model_id=adapter["sma_module_type_id"],
        hw_version=adapter["idf_version"],
        sw_version=adapter["fw_version"],
        manufacturer="Österreichs E-Wirtschaft",
        configuration_url=entry.data[CONF_HOST],
    )
    # meter
    meter = status_coordinator.data["meter"]
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(entry.domain, f"{entry.entry_id}-meter")},
        translation_key="meter",
        model=meter["supplier"],
        model_id=meter["supplier_id"],
        manufacturer=f"{meter['manufacturer']} {meter['name']}",
        serial_number=get_meter_number(measurement_coordinator.data),
        via_device=(entry.domain, f"{entry.entry_id}-sma"),
    )

    return True


async def _async_setup_mqtt_entry(hass: HomeAssistant, entry: OeSmaConfigEntry) -> bool:
    """Set up this integration using MQTT configuration."""
    if not await mqtt_integration.async_wait_for_mqtt_client(hass):
        msg = "MQTT integration is not available."
        LOGGER.warning(msg)
        raise ConfigEntryNotReady(msg)

    message_handler = OeSmaMqttMessageHandler(hass, entry)

    entry.runtime_data = OeSmaData(
        type=OeSmaApiType.MQTT,
        integration=async_get_loaded_integration(hass, entry.domain),
        mqtt_message_handler=message_handler,
    )

    unsubscribe_handler = await mqtt_integration.async_subscribe(
        hass,
        topic=entry.data[CONF_TOPIC],
        msg_callback=message_handler.message_received,
        qos=entry.data[CONF_OPTIONS][CONF_QOS] or 0,
    )
    entry.async_on_unload(unsubscribe_handler)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: OeSmaConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: OeSmaConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    config_entry: OeSmaConfigEntry,
    device_entry: dr.DeviceEntry,  # noqa: ARG001 Unused function argument: `device_entry`
) -> bool:
    """Remove a config entry from a device."""
    runtime_data = config_entry.runtime_data

    match runtime_data.type:
        case OeSmaApiType.JSON:
            return not runtime_data.json_measurement_coordinator.last_update_success
        case OeSmaApiType.MQTT:
            return True

    return False
