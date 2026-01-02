import socket
from typing import Any

import aiohttp
import async_timeout


class SMAApiClientError(Exception):
    """General Smart Meter API client error."""


class SMAApiClientCommunicationError(SMAApiClientError):
    """Exception to indicate a communication error."""


class SMAApiClientAuthenticationError(SMAApiClientError):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise SMAApiClientAuthenticationError(msg)
    elif response.status == 404:
        msg = "Not found"
        raise SMAApiClientCommunicationError(msg)
    response.raise_for_status()


class SMAApiClient:
    """Client for the Smart Meter Adapter."""

    def __init__(
            self,
            host: str,
            token: str,
            session: aiohttp.ClientSession,
            version: str = "v1",
    ) -> None:
        self._host = host
        self._token = token
        self._session = session
        self._version = version

    async def async_get_measurement(self) -> Any:
        """Get the current measurements from the Smart Meter."""
        return await self._get_data(endpoint="measurement.json")

    async def async_get_status(self) -> Any:
        """Get the status of the Smart Meter Adapter."""
        return await self._get_data(endpoint="status.json")

    async def _get_data(
            self,
            endpoint: str,
    ) -> Any:
        """Call the JSON API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(
                    url=f'{self._host}/api/{self._version}/{endpoint}',
                    headers={
                        "Authorization": f"TOKEN {self._token}",
                        "Content-Type": "application/json",
                    }
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise SMAApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise SMAApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Error with the API client! - {exception}"
            raise SMAApiClientError(
                msg,
            ) from exception
