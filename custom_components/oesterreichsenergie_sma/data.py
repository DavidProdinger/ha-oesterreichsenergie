"""The Oesterreichsenergie Smart-Meter-Adapter integration data class."""

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.loader import Integration

from .api import SMAApiClient
from .const import OeSmaApiType
from .coordinator import (
    OeSmaMeasurementDataUpdateCoordinator,
    OeSmaMqttDataUpdateCoordinator,
    OeSmaStatusDataUpdateCoordinator,
)

type OeSmaConfigEntry = ConfigEntry[OeSmaData]


@dataclass
class OeSmaData:
    """Data for the Oesterreichsenergie Smart-Meter-Adapter."""

    type: OeSmaApiType
    integration: Integration

    # JSON specific
    json_client: SMAApiClient | None = None
    json_measurement_coordinator: OeSmaMeasurementDataUpdateCoordinator | None = None
    json_status_coordinator: OeSmaStatusDataUpdateCoordinator | None = None

    # MQTT specific
    mqtt_coordinator: OeSmaMqttDataUpdateCoordinator | None = None
