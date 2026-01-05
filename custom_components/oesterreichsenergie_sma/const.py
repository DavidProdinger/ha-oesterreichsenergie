"""Constants for oesterreichsenergie_sma."""

from enum import StrEnum
from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "oesterreichsenergie_sma"


class OeSmaApiType(StrEnum):
    """Supported API types of the Smart Meter Adapter."""

    JSON = "json"
    MQTT = "mqtt"
    MODBUS = "modbus"
