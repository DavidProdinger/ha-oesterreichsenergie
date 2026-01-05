"""Representation of Oesterreichsenergie Smart-Meter-Adapter entities."""

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import (
    OeSmaDataUpdateCoordinator,
    OeSmaMeasurementDataUpdateCoordinator,
)


class OeSMAMeasurementEntityBase(CoordinatorEntity[OeSmaDataUpdateCoordinator]):
    """Basic entity for Oesterreichsenergie Smart-Meter-Adapter."""

    _attr_has_entity_name = True

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
                    f"{coordinator.config_entry.options.get('type')}-{coordinator.config_entry.entry_id}-meter",
                )
            },
        )
