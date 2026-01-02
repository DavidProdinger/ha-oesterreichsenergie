from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_VERIFY_SSL, CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import TextSelector, TextSelectorType, TextSelectorConfig
from homeassistant.util import slugify

from .api import (
    SMAApiClient,
    SMAApiClientError,
    SMAApiClientAuthenticationError,
    SMAApiClientCommunicationError,
)
from .const import DOMAIN, LOGGER

DATA_SCHEMA_SETUP = vol.Schema({
    vol.Required(CONF_HOST): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
    vol.Required(CONF_VERIFY_SSL, default=False): bool,
    vol.Required(CONF_TOKEN): TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD)),
})


class SMAConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Smart Meter Adapter."""
    VERSION = 1

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ):
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            # prepend https:// if missing
            if not user_input[CONF_HOST].startswith("http"):
                user_input[CONF_HOST] = "https://" + user_input[CONF_HOST]

            user_input[CONF_HOST] = user_input[CONF_HOST].strip('/')

            try:
                status = await self._get_status(
                    host=user_input[CONF_HOST],
                    verify_ssl=user_input[CONF_VERIFY_SSL],
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
                    unique_id=slugify(status['wifi']['mac'] or status['name'] or user_input[CONF_HOST])
                )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=status['name'] or f"Smart Meter Adapter - {user_input[CONF_HOST]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA_SETUP,
            errors=_errors,
        )

    async def _get_status(
            self,
            host: str,
            verify_ssl: bool,
            token: str,
    ) -> Any:
        client = SMAApiClient(
            host=host,
            token=token,
            session=async_create_clientsession(self.hass, verify_ssl=verify_ssl),
        )
        return await client.async_get_status()
