"""
The Österreichsenergie Smart-Meter-Adapter integration with Home Assistant.

For more details about this integration, please refer to
https://github.com/DavidProdinger/ha-oesterreichsenergie
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import Platform, CONF_HOST, CONF_TOKEN, CONF_VERIFY_SSL
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import SMAApiClient
from .const import DOMAIN, LOGGER
from .coordinator import SMAMeasurementDataUpdateCoordinator, SMAStatusDataUpdateCoordinator
from .data import SMAData
from .obis import get_meter_number

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import SMAConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
        hass: HomeAssistant,
        entry: SMAConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    measurement_coordinator = SMAMeasurementDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=15),
    )
    status_coordinator = SMAStatusDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )

    entry.runtime_data = SMAData(
        client=SMAApiClient(
            host=entry.data[CONF_HOST],
            token=entry.data[CONF_TOKEN],
            session=async_get_clientsession(hass, verify_ssl=entry.data[CONF_VERIFY_SSL]),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        measurement_coordinator=measurement_coordinator,
        status_coordinator=status_coordinator,
    )

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await measurement_coordinator.async_config_entry_first_refresh()
    await status_coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # create devices
    device_registry = dr.async_get(hass)
    # adapter
    adapter = status_coordinator.data
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        entry_type=dr.DeviceEntryType.SERVICE,
        connections={(dr.CONNECTION_NETWORK_MAC, adapter['wifi']['mac'])},
        identifiers={(entry.domain, f"{entry.entry_id}-sma")},
        name="Smart-Meter-Adapter (SMA)",
        model=adapter['sma_module_type'],
        model_id=adapter['sma_module_type_id'],
        hw_version=adapter['idf_version'],
        sw_version=adapter['fw_version'],
        manufacturer="Österreichs E‑Wirtschaft",
        configuration_url=entry.data[CONF_HOST],
    )
    # meter
    meter = status_coordinator.data['meter']
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(entry.domain, f"{entry.entry_id}-meter")},
        name="Smart Meter",
        model=meter['supplier'],
        model_id=meter['supplier_id'],
        manufacturer=f"{meter['manufacturer']} {meter['name']}",
        serial_number=get_meter_number(measurement_coordinator.data),
        via_device=(entry.domain, f"{entry.entry_id}-sma"),
    )

    return True


async def async_unload_entry(
        hass: HomeAssistant,
        entry: SMAConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
        hass: HomeAssistant,
        entry: SMAConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
