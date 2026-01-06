"""Representation of Oesterreichsenergie Smart-Meter-Adapter sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfReactiveEnergy,
)
from homeassistant.core import HomeAssistant, callback

from .const import OeSmaApiType
from .entity import (
    OeSmaEntityDescription,
    OeSmaMeasurementEntityBase,
    OeSmaMqttEntityBase,
)

if TYPE_CHECKING:
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OeSmaMeasurementDataUpdateCoordinator
    from .data import OeSmaConfigEntry


PARALLEL_UPDATES = 1


@dataclass(frozen=True)
class OeSmaSensorEntityDescription(OeSmaEntityDescription, SensorEntityDescription):
    """Describes Oesterreichsenergie Smart-Meter-Adapter sensor entities."""


ENTITY_DESCRIPTIONS = [
    OeSmaSensorEntityDescription(
        key="1-0:1.8.0",
        translation_key="active_energy_import",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:2.8.0",
        translation_key="active_energy_export",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:3.8.0",
        translation_key="reactive_energy_import",
        device_class=SensorDeviceClass.REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfReactiveEnergy.VOLT_AMPERE_REACTIVE_HOUR,
        suggested_unit_of_measurement=UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
        entity_registry_enabled_default=False,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:4.8.0",
        translation_key="reactive_energy_export",
        device_class=SensorDeviceClass.REACTIVE_ENERGY,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfReactiveEnergy.VOLT_AMPERE_REACTIVE_HOUR,
        suggested_unit_of_measurement=UnitOfReactiveEnergy.KILO_VOLT_AMPERE_REACTIVE_HOUR,
        entity_registry_enabled_default=False,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:1.7.0",
        translation_key="power_import",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.WATT,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:2.7.0",
        translation_key="power_export",
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPower.WATT,
        suggested_unit_of_measurement=UnitOfPower.WATT,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:32.7.0",
        translation_key="voltage_l1",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:52.7.0",
        translation_key="voltage_l2",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:72.7.0",
        translation_key="voltage_l3",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_unit_of_measurement=UnitOfElectricPotential.VOLT,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:31.7.0",
        translation_key="current_l1",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:51.7.0",
        translation_key="current_l2",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
    OeSmaSensorEntityDescription(
        key="1-0:71.7.0",
        translation_key="current_l3",
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
    ),
]

DIAGNOSTICS_ENTITY_DESCRIPTIONS = [
    OeSmaSensorEntityDescription(
        key="0-0:1.0.0",
        translation_key="meter_date",
        device_class=SensorDeviceClass.DATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_visible_default=True,
        entity_registry_enabled_default=False,
        icon="mdi:calendar-clock",
        obis_data_key="time",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OeSmaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    match entry.runtime_data.type:
        case OeSmaApiType.JSON:
            await async_setup_entry_json(hass, entry, async_add_entities)
        case OeSmaApiType.MQTT:
            await async_setup_entry_mqtt(hass, entry, async_add_entities)


async def async_setup_entry_json(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OeSmaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform for JSON API."""
    async_add_entities(
        OeSmaMeasurementSensor(
            coordinator=entry.runtime_data.json_measurement_coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS + DIAGNOSTICS_ENTITY_DESCRIPTIONS
    )


async def async_setup_entry_mqtt(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OeSmaConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform for MQTT API."""
    entry.runtime_data.mqtt_message_handler.register_platform(
        async_add_entities,
        OeSmaMqttSensor,
        ENTITY_DESCRIPTIONS + DIAGNOSTICS_ENTITY_DESCRIPTIONS,
    )


class OeSmaMeasurementSensor(OeSmaMeasurementEntityBase, SensorEntity):
    """Representation of a Smart Meter Adapter measurement sensor."""

    def __init__(
        self,
        coordinator: OeSmaMeasurementDataUpdateCoordinator,
        entity_description: OeSmaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )
        self.translation_key = (
            entity_description.translation_key or entity_description.key
        )

        if coordinator.data is not None:
            self._attr_native_value = coordinator.data[entity_description.key][
                entity_description.obis_data_key
            ]

    @callback
    def _handle_coordinator_update(self) -> None:
        if not self._verified_state_writable:
            return

        value = self.coordinator.data[self.entity_description.key][
            self.entity_description.obis_data_key
        ]

        if self.entity_description.device_class in [
            SensorDeviceClass.TIMESTAMP,
            SensorDeviceClass.DATE,
        ]:
            local_tz = ZoneInfo(self.hass.config.time_zone)
            self._attr_native_value = datetime.fromtimestamp(value, tz=local_tz)
        else:
            self._attr_native_value = value

        self.async_write_ha_state()


class OeSmaMqttSensor(OeSmaMqttEntityBase, SensorEntity):
    """Representation of a Smart Meter Adapter MQTT sensor."""

    def __init__(
        self,
        entry: OeSmaConfigEntry,
        meter_number: str,
        entity_description: OeSmaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entry, meter_number, entity_description)

    @callback
    def update_data(self, measurement: dict[str, Any]) -> None:
        """Update the sensor data."""
        if not self._verified_state_writable:
            return

        if self.entity_description.key in measurement:
            value = measurement[self.entity_description.key][
                self.entity_description.obis_data_key
            ]

            if self.entity_description.device_class in [
                SensorDeviceClass.TIMESTAMP,
                SensorDeviceClass.DATE,
            ]:
                local_tz = ZoneInfo(self.hass.config.time_zone)
                self._attr_native_value = datetime.fromtimestamp(value, tz=local_tz)
            else:
                self._attr_native_value = value

            self.async_write_ha_state()
