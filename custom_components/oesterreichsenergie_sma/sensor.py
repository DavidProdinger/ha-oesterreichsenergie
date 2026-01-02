from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import SensorEntityDescription, SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfReactiveEnergy, UnitOfPower, UnitOfElectricPotential, \
    UnitOfElectricCurrent, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import LOGGER
from .coordinator import SMAMeasurementDataUpdateCoordinator
from .data import SMAConfigEntry
from .entity import OeSMAMeasurementEntityBase


@dataclass(frozen=True)
class OeSMASensorEntityDescription(SensorEntityDescription):
    """Describes Oesterreichsenergie Smart-Meter-Adapter sensor entities."""


ENTITY_DESCRIPTIONS = [
    OeSMASensorEntityDescription(
        key="1-0:1.8.0",
        name="Forward active energy +A",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    OeSMASensorEntityDescription(
        key="1-0:2.8.0",
        name="Reverse active energy -A",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    OeSMASensorEntityDescription(
        key="1-0:3.8.0",
        name="Import reactive energy +R",
        device_class=SensorDeviceClass.REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfReactiveEnergy.VOLT_AMPERE_REACTIVE_HOUR,
        suggested_unit_of_measurement=UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
    ),
    OeSMASensorEntityDescription(
        key="1-0:4.8.0",
        name="Export reactive energy -R",
        device_class=SensorDeviceClass.REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfReactiveEnergy.VOLT_AMPERE_REACTIVE_HOUR,
        suggested_unit_of_measurement=UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
    ),
    OeSMASensorEntityDescription(
        key="1-0:1.7.0",
        name="Instantaneous forward active power +P",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.WATT,
    ),
    OeSMASensorEntityDescription(
        key="1-0:2.7.0",
        name="Instantaneous reverse active power -P",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.WATT,
    ),
    OeSMASensorEntityDescription(
        key="1-0:32.7.0",
        name="Instantaneous voltage L1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OeSMASensorEntityDescription(
        key="1-0:52.7.0",
        name="Instantaneous voltage L2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OeSMASensorEntityDescription(
        key="1-0:72.7.0",
        name="Instantaneous voltage L3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OeSMASensorEntityDescription(
        key="1-0:31.7.0",
        name="Instantaneous current L1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    OeSMASensorEntityDescription(
        key="1-0:51.7.0",
        name="Instantaneous current L2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    OeSMASensorEntityDescription(
        key="1-0:71.7.0",
        name="Instantaneous current L3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),

]


async def async_setup_entry(
        hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
        entry: SMAConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        OeSMAMeasurementSensor(
            coordinator=entry.runtime_data.measurement_coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )

    async_add_entities({
        OeSMAMeterDateSensor(
            coordinator=entry.runtime_data.measurement_coordinator,
            entity_description=OeSMASensorEntityDescription(
                key="0-0:1.0.0",
                name="Meter date",
                device_class=SensorDeviceClass.DATE,
                entity_category=EntityCategory.DIAGNOSTIC,
                entity_registry_visible_default=False,
                entity_registry_enabled_default=False,
                icon="mdi:calendar-clock",
            ),
        ),
    })


class OeSMAMeasurementSensor(OeSMAMeasurementEntityBase, SensorEntity):
    def __init__(
            self,
            coordinator: SMAMeasurementDataUpdateCoordinator,
            entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        self._attr_native_value = coordinator.data[entity_description.key]['value']

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.coordinator.data[self.entity_description.key]['value']
        self.async_write_ha_state()


class OeSMAMeterDateSensor(OeSMAMeasurementEntityBase, SensorEntity):
    def __init__(
            self,
            coordinator: SMAMeasurementDataUpdateCoordinator,
            entity_description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        self.set_value(coordinator.data[entity_description.key]['time'])

    def set_value(self, value: str | float) -> None:
        local_tz = ZoneInfo(self.coordinator.hass.config.time_zone)
        self._attr_native_value = datetime.fromtimestamp(value, tz=local_tz)

    @callback
    def _handle_coordinator_update(self) -> None:
        self.set_value(self.coordinator.data[self.entity_description.key]['time'])
        self.async_write_ha_state()
