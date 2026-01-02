from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

from .api import SMAApiClient
from .coordinator import SMAMeasurementDataUpdateCoordinator, SMAStatusDataUpdateCoordinator

type SMAConfigEntry = ConfigEntry[SMAData]


@dataclass
class SMAData:
    """Data for the Oesterreichsenergie Smart-Meter-Adapter."""

    client: SMAApiClient
    measurement_coordinator: SMAMeasurementDataUpdateCoordinator
    status_coordinator: SMAStatusDataUpdateCoordinator
    integration: Integration
