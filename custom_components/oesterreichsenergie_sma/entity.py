"""Representation of Oesterreichsenergie Smart-Meter-Adapter entities."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import (
    OeSmaDataUpdateCoordinator,
    OeSmaMeasurementDataUpdateCoordinator,
)

if TYPE_CHECKING:
    from .data import OeSmaConfigEntry


@dataclass(frozen=True)
class OeSmaEntityDescription(EntityDescription):
    """Describes Oesterreichsenergie Smart-Meter-Adapter entities."""

    has_entity_name: bool = True
    obis_data_key: str | None = "value"


class OeSmaMeasurementEntityBase(CoordinatorEntity[OeSmaDataUpdateCoordinator], ABC):
    """Basic entity for Oesterreichsenergie Smart-Meter-Adapter."""

    _attr_has_entity_name = True
    entity_description: OeSmaEntityDescription

    def __init__(
        self,
        coordinator: OeSmaMeasurementDataUpdateCoordinator,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)

        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    f"{coordinator.config_entry.entry_id}-meter",
                )
            },
        )


class OeSmaMqttEntityBase(Entity, ABC):
    """Basic entity for Oesterreichsenergie Smart-Meter-Adapter MQTT Entities."""

    _attr_has_entity_name = True
    entity_description: OeSmaEntityDescription

    def __init__(
        self,
        entry: OeSmaConfigEntry,
        meter_number: str,
        entity_description: OeSmaEntityDescription,
    ) -> None:
        """Initialize the entity."""
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{entry.entry_id}_{meter_number}_{entity_description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(entry.domain, f"mqtt_{meter_number}")},
            serial_number=meter_number,
        )
