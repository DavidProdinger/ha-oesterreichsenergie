"""Diagnostics support for Oesterreichsenergie Smart-Meter-Adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_TOKEN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import OeSmaConfigEntry

TO_REDACT = {CONF_TOKEN}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: OeSmaConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    diag_data = {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "type": entry.options.get("type"),
    }

    if entry.runtime_data.json_measurement_coordinator:
        diag_data["json_measurement"] = (
            entry.runtime_data.json_measurement_coordinator.data
        )

    if entry.runtime_data.json_status_coordinator:
        diag_data["json_status"] = entry.runtime_data.json_status_coordinator.data

    if entry.runtime_data.mqtt_message_handler:
        diag_data["mqtt_meters"] = dict.fromkeys(
            entry.runtime_data.mqtt_message_handler.known_meters
        )

    return diag_data
