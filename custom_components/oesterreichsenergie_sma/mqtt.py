"""MQTT message handler for Oesterreichsenergie Smart-Meter-Adapter."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN, LOGGER
from .obis import OBIS_CODES, OBIS_SCHEMA, get_meter_number

if TYPE_CHECKING:
    from homeassistant.components.mqtt import ReceiveMessage
    from homeassistant.helpers.device_registry import DeviceRegistry
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .data import OeSmaConfigEntry
    from .entity import OeSmaEntityDescription, OeSmaMqttEntityBase


SCHEMA_MQTT_MESSAGE = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required(
            vol.Any(*OBIS_CODES.keys(), msg="Invalid OBIS code provided")
        ): OBIS_SCHEMA,
    },
    extra=vol.ALLOW_EXTRA,
)


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
        self.last_update: dict[str, float] = {}

        # Check for stale meters every minute
        entry.async_on_unload(
            async_track_time_interval(
                hass, self._check_stale_meters, timedelta(minutes=1)
            )
        )

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
            SCHEMA_MQTT_MESSAGE(measurement)
        except json.JSONDecodeError as exc:
            LOGGER.error("Failed to parse MQTT message payload: %s", exc)
            return
        except vol.Invalid as exc:
            LOGGER.warning("Invalid MQTT message payload: %s", exc)
            return

        meter_number = get_meter_number(measurement)
        if meter_number is None:
            return

        self.last_update[meter_number] = time.time()

        if meter_number not in self.known_meters:
            self._register_new_meter(meter_number, measurement)

        # Update entities
        if meter_number in self.entities:
            for entity in self.entities[meter_number]:
                entity.set_available()
                if hasattr(entity, "update_data"):
                    entity.update_data(measurement)

    def _register_new_meter(self, meter_number: str, measurement: dict) -> None:
        """Register a new meter and its entities."""
        LOGGER.debug("Registering new meter: %s", meter_number)
        self.known_meters.add(meter_number)
        self.entities[meter_number] = []

        self.device_registry.async_get_or_create(
            config_entry_id=self.entry.entry_id,
            identifiers={(DOMAIN, f"mqtt_{meter_number}")},
            name=f"Smart Meter - {measurement['name']}",
            model=meter_number,
            serial_number=meter_number,
        )

        for async_add_entities, entity_class, descriptions in self.platforms:
            new_entities = []
            for description in descriptions:
                entity = entity_class(self.entry, meter_number, description)
                entity.set_available()
                new_entities.append(entity)
                self.entities[meter_number].append(entity)
            async_add_entities(new_entities)

    @callback
    def _check_stale_meters(self, _now: datetime) -> None:
        """Check for meters that haven't sent data for 1 hour."""
        now = time.time()
        stale_threshold = 3600  # 1 hour in seconds

        for meter_number, last_update in self.last_update.items():
            if now - last_update > stale_threshold and meter_number in self.entities:
                for entity in self.entities[meter_number]:
                    if entity.available:
                        entity.set_available(available=False)
                        entity.async_write_ha_state()
