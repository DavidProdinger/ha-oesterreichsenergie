"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import slugify

from .api import (
    SMAApiClientAuthenticationError,
    SMAApiClientError,
)
from .const import DOMAIN, LOGGER
from .obis import get_meter_number

if TYPE_CHECKING:
    import logging

    from homeassistant.components.mqtt import ReceiveMessage

    from .data import OeSmaConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class OeSmaDataUpdateCoordinator(ABC, DataUpdateCoordinator):
    """Class to fetch data from the API."""

    config_entry: OeSmaConfigEntry

    @abstractmethod
    async def _update_method(self) -> Any:
        """Update function to call."""

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            return await self._update_method()
        except SMAApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except SMAApiClientError as exception:
            raise UpdateFailed(exception) from exception


class OeSmaMeasurementDataUpdateCoordinator(OeSmaDataUpdateCoordinator):
    """Class to fetch Smart Meter Adapter measurement data."""

    async def _update_method(self) -> Any:
        return await self.config_entry.runtime_data.json_client.async_get_measurement()


class OeSmaStatusDataUpdateCoordinator(OeSmaDataUpdateCoordinator):
    """Class to fetch Smart Meter Adapter status data."""

    async def _update_method(self) -> Any:
        return await self.config_entry.runtime_data.json_client.async_get_status()


class OeSmaMqttDataUpdateCoordinator(OeSmaDataUpdateCoordinator):
    """Class to fetch Smart Meter Adapter MQTT data."""

    def __init__(
        self, hass: HomeAssistant, logger: logging.Logger, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize the coordinator and set always_update to False."""
        super().__init__(hass, logger, *args, **kwargs)
        self.device_registry = dr.async_get(hass)

    async def _update_method(self) -> Any:
        """Update here the device."""
        if self.data is not None:
            meter_number = get_meter_number(self.data)
            self.device_registry.async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                identifiers={(DOMAIN, f"mqtt_{slugify(meter_number)}")},
                name=self.data["name"],
                serial_number=meter_number,
            )

    async def _async_update_data(self) -> Any:
        msg = "Update method not implemented"
        raise NotImplementedError(msg)

    @callback
    def message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        try:
            measurement = json.loads(msg.payload)
        except json.JSONDecodeError as exc:
            LOGGER.error("Failed to parse MQTT message payload: %s", exc)
            return
        else:
            # todo: multiple different devices on the same topic could be possible
            self.async_set_updated_data(measurement)
