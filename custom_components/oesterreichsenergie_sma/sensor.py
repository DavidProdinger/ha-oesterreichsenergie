from dataclasses import dataclass

from homeassistant.components.sensor import SensorEntityDescription, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import SMAMeasurementDataUpdateCoordinator
from .data import SMAConfigEntry
from .entity import OeSMAMeasurementEntityBase


@dataclass(frozen=True)
class OeSMASensorEntityDescription(SensorEntityDescription):
    """Describes Oesterreichsenergie Smart-Meter-Adapter sensor entities."""


ENTITY_DESCRIPTIONS = [
    OeSMASensorEntityDescription(
        # OBIS code 1.8.0
        key="1-0:1.8.0",
        name="Positive active energy"
    ),
]


async def async_setup_entry(
        hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
        entry: SMAConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        OeSMAMeasurementEnergySensor(
            coordinator=entry.runtime_data.measurement_coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class OeSMAMeasurementEnergySensor(OeSMAMeasurementEntityBase, SensorEntity):
    def __init__(
            self,
            coordinator: SMAMeasurementDataUpdateCoordinator,
            entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_native_value = coordinator.data[entity_description.key]['value']
