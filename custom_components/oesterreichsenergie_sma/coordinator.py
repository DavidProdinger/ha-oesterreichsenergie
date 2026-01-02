"""DataUpdateCoordinator for integration_blueprint."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SMAApiClientAuthenticationError,
    SMAApiClientError,
)

if TYPE_CHECKING:
    from .data import SMAConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class SMADataUpdateCoordinatorBase(ABC, DataUpdateCoordinator):
    """Class to fetch data from the API."""

    config_entry: SMAConfigEntry

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


class SMAMeasurementDataUpdateCoordinator(SMADataUpdateCoordinatorBase):
    """Class to fetch Smart Meter Adapter measurement data."""

    async def _update_method(self) -> Any:
        return await self.config_entry.runtime_data.client.async_get_measurement()


class SMAStatusDataUpdateCoordinator(SMADataUpdateCoordinatorBase):
    """Class to fetch Smart Meter Adapter status data."""

    async def _update_method(self) -> Any:
        return await self.config_entry.runtime_data.client.async_get_status()
