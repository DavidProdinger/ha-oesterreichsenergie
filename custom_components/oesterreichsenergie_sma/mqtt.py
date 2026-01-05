"""MQTT message handler for Oesterreichsenergie Smart-Meter-Adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, LOGGER
from .obis import get_meter_number

if TYPE_CHECKING:
    from homeassistant.components.mqtt import ReceiveMessage
    from homeassistant.helpers.device_registry import DeviceRegistry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OeSmaConfigEntry
    from .entity import OeSmaEntityDescription, OeSmaMqttEntityBase


class OeSmaMqttMessageHandler:
    """MQTT message handler for Oesterreichsenergie Smart-Meter-Adapter."""

    def __init__(self, hass: HomeAssistant, entry: OeSmaConfigEntry) -> None:
        """Initialize the message handler."""
        self.hass = hass
        self.entry = entry
        self.platforms: list[
            tuple[
                AddEntitiesCallback,
                type[OeSmaMqttEntityBase],
                list[OeSmaEntityDescription],
            ]
        ] = []

        self.device_registry: DeviceRegistry = dr.async_get(hass)
        self.known_meters: set[str] = set()
        self.entities: dict[str, list[OeSmaMqttEntityBase]] = {}

    @callback
    def register_platform(
        self,
        async_add_entities: AddEntitiesCallback,
        entity_class: type[OeSmaMqttEntityBase],
        descriptions: list[OeSmaEntityDescription],
    ) -> None:
        """Register MQTT entity platforms."""
        self.platforms.append((async_add_entities, entity_class, descriptions))

    @callback
    def message_received(self, msg: ReceiveMessage) -> None:
        """Handle new MQTT messages."""
        try:
            measurement = json.loads(msg.payload)
        except json.JSONDecodeError as exc:
            LOGGER.error("Failed to parse MQTT message payload: %s", exc)
            return

        meter_number = get_meter_number(measurement)
        if meter_number is None:
            return

        if meter_number not in self.known_meters:
            self._register_new_meter(meter_number)

        # Update entities
        if meter_number in self.entities:
            for entity in self.entities[meter_number]:
                if hasattr(entity, "update_data"):
                    entity.update_data(measurement)

    def _register_new_meter(self, meter_number: str) -> None:
        """Register a new meter and its entities."""
        LOGGER.debug("Registering new meter: %s", meter_number)
        self.known_meters.add(meter_number)
        self.entities[meter_number] = []

        self.device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, f"mqtt_{meter_number}")},
            name=f"{meter_number}",
            serial_number=meter_number,
        )

        for async_add_entities, entity_class, descriptions in self.platforms:
            new_entities = []
            for description in descriptions:
                entity = entity_class(self.entry, meter_number, description)
                new_entities.append(entity)
                self.entities[meter_number].append(entity)
            async_add_entities(new_entities)
