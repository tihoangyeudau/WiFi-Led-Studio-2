import logging

from aiohttp import web

from wls.api import RestEndpoint
from wls.utils import async_fire_and_forget

_LOGGER = logging.getLogger(__name__)


class FindDevicesEndpoint(RestEndpoint):
    """REST end-point for detecting and adding rml devices"""

    ENDPOINT_PATH = "/api/find_devices"

    async def post(self) -> web.Response:
        """Find and add all RML devices on the LAN"""

        def handle_exception(future):
            # Ignore exceptions, these will be raised when a device is found that already exists
            exc = future.exception()

        async_fire_and_forget(
            self._wls.devices.find_rml_devices(),
            loop=self._wls.loop,
            exc_handler=handle_exception,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)
