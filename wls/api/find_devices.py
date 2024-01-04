import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.utils import async_fire_and_forget, set_name_to_icon

_LOGGER = logging.getLogger(__name__)


def handle_exception(future):
    # Ignore exceptions, these will be raised when a device is found that already exists
    exc = future.exception()


class FindDevicesEndpoint(RestEndpoint):
    """REST end-point for detecting and adding rml devices"""

    ENDPOINT_PATH = "/api/find_devices"

    async def post(self, request) -> web.Response:
        """Find and add all RML devices on the LAN"""
        try:
            data = await request.json()
        except JSONDecodeError:
            return await self.json_decode_error()

        name_to_icon = data.get("name_to_icon")

        if name_to_icon is None:
            response = {
                "status": "failed",
                "reason": 'Required attribute "name_to_icon" was not provided',
            }
            return web.json_response(data=response, status=400)
        set_name_to_icon(name_to_icon)

        async_fire_and_forget(
            self._wls.zeroconf.discover_rml_devices(),
            loop=self._wls.loop,
            exc_handler=handle_exception,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)

    async def get(self) -> web.Response:
        """Handle HTTP GET requests"""
        async_fire_and_forget(
            self._wls.zeroconf.discover_rml_devices(),
            loop=self._wls.loop,
            exc_handler=handle_exception,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)