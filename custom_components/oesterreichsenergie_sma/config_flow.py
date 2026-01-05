"""Configuration flow for Smart Meter Adapter."""

from typing import Any

import voluptuous as vol
from homeassistant.components import mqtt
from homeassistant.components.mqtt import CONF_QOS, CONF_TOPIC, valid_subscribe_topic
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_OPTIONS,
    CONF_TOKEN,
    CONF_VERIFY_SSL,
)
from homeassistant.data_entry_flow import SectionConfig, section
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo
from homeassistant.util import slugify

from .api import (
    SMAApiClient,
    SMAApiClientAuthenticationError,
    SMAApiClientCommunicationError,
    SMAApiClientError,
)
from .const import DOMAIN, LOGGER, OeSmaApiType

DATA_SCHEMA_SETUP_JSON = vol.Schema(
    {
        vol.Required(CONF_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.URL)
        ),
        vol.Required(CONF_TOKEN): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_OPTIONS): section(
            vol.Schema(
                {
                    vol.Required(CONF_VERIFY_SSL, default=False): bool,
                }
            ),
            SectionConfig(collapsed=True),
        ),
    }
)

DATA_SCHEMA_SETUP_MQTT = vol.Schema(
    {
        vol.Required(CONF_TOPIC, default="sma"): TextSelector(),
        vol.Optional(CONF_OPTIONS): section(
            vol.Schema(
                {
                    vol.Optional(CONF_QOS, default=0): int,
                }
            ),
            SectionConfig(collapsed=True),
        ),
    }
)


class SMAConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow for Smart Meter Adapter."""

    VERSION = 1

    async def async_step_user(
        self,
        _: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        # noinspection PyTypeChecker
        return self.async_show_menu(
            step_id="user",
            menu_options=["json", "mqtt_manual"],
        )

    async def async_step_json(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the setup flow for the JSON API initialized by the user."""
        _errors = {}
        if user_input is not None:
            # prepend https:// if missing
            if not user_input[CONF_HOST].startswith("http"):
                user_input[CONF_HOST] = "https://" + user_input[CONF_HOST]

            user_input[CONF_HOST] = user_input[CONF_HOST].strip("/")

            try:
                status = await self._get_status(
                    host=user_input[CONF_HOST],
                    verify_ssl=user_input[CONF_OPTIONS][CONF_VERIFY_SSL],
                    token=user_input[CONF_TOKEN],
                )
            except SMAApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except SMAApiClientCommunicationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "connection"
            except SMAApiClientError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    unique_id=slugify(
                        status["wifi"]["mac"] or status["name"] or user_input[CONF_HOST]
                    )
                )
                self._abort_if_unique_id_configured()

                # noinspection PyTypeChecker
                return self.async_create_entry(
                    title=status["name"]
                    or f"Smart Meter Adapter - {user_input[CONF_HOST]}",
                    data=user_input,
                    options={"type": OeSmaApiType.JSON},
                )

        # noinspection PyTypeChecker
        return self.async_show_form(
            step_id="json",
            data_schema=DATA_SCHEMA_SETUP_JSON,
            errors=_errors,
        )

    async def _get_status(
        self,
        *,
        host: str,
        verify_ssl: bool,
        token: str,
    ) -> Any:
        """Get the status of the Smart Meter Adapter via JSON API."""
        client = SMAApiClient(
            host=host,
            token=token,
            session=async_create_clientsession(self.hass, verify_ssl=verify_ssl),
        )
        return await client.async_get_status()

    async def async_step_mqtt(
        self, discovery_info: MqttServiceInfo
    ) -> ConfigFlowResult:
        """Handle the setup flow for the MQTT discovery."""
        if self._async_in_progress() or any(
            e.unique_id == OeSmaApiType.MQTT for e in self._async_current_entries()
        ):
            # noinspection PyTypeChecker
            return self.async_abort(reason="single_instance_allowed")

        await self.async_set_unique_id(unique_id=OeSmaApiType.MQTT)

        # noinspection PyTypeChecker
        return await self.async_step_mqtt_manual(topic_hint=discovery_info.topic)

    async def async_step_mqtt_manual(
        self, user_input: dict[str, Any] | None = None, topic_hint: str | None = None
    ) -> ConfigFlowResult:
        """Handle the setup flow for the MQTT discovery or from the user step."""
        _errors = {}

        if not mqtt.mqtt_config_entry_enabled(self.hass):
            msg = "MQTT integration is not enabled."
            LOGGER.warning(msg)
            # noinspection PyTypeChecker
            return self.async_abort(reason="mqtt_not_enabled")

        if user_input is not None:
            try:
                user_input[CONF_TOPIC] = valid_subscribe_topic(user_input[CONF_TOPIC])
            except (ValueError, vol.Error, vol.Invalid):
                _errors[CONF_TOPIC] = "invalid_subscribe_topic"
            else:
                await self.async_set_unique_id(unique_id=OeSmaApiType.MQTT)
                self._abort_if_unique_id_configured()

                # noinspection PyTypeChecker
                return self.async_create_entry(
                    title="MQTT",
                    data=user_input,
                    options={"type": OeSmaApiType.MQTT},
                )

        # noinspection PyTypeChecker
        return self.async_show_form(
            step_id="mqtt_manual",
            data_schema=self.add_suggested_values_to_schema(
                DATA_SCHEMA_SETUP_MQTT, {CONF_TOPIC: topic_hint}
            ),
            errors=_errors,
        )
