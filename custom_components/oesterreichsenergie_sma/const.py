"""Constants for oesterreichsenergie_sma."""

from __future__ import annotations

from enum import StrEnum
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "oesterreichsenergie_sma"

DEFAULT_TOPIC = "sma"
REDACTED_TOKEN_PLACEHOLDER = "###__REDACTED__###"  # noqa: S105


class OeSmaApiType(StrEnum):
    """Supported API types of the Smart Meter Adapter."""

    JSON = "json"
    MQTT = "mqtt"
    MODBUS = "modbus"
