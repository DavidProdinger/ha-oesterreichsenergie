from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SMADataUpdateCoordinatorBase, SMAMeasurementDataUpdateCoordinator


class OeSMAMeasurementEntityBase(CoordinatorEntity[SMADataUpdateCoordinatorBase]):
    def __init__(
            self,
            coordinator: SMAMeasurementDataUpdateCoordinator,
    ) -> None:
        super().__init__(coordinator)

        self._attr_unique_id = coordinator.config_entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(
                coordinator.config_entry.domain,
                f"{coordinator.config_entry.entry_id}-meter",
            )},
        )
