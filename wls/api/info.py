import logging

from aiohttp import web

from wls.api import RestEndpoint
from wls.consts import PROJECT_VERSION

_LOGGER = logging.getLogger(__name__)


class InfoEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/info"

    async def get(self) -> web.Response:
        response = {
            "url": self._wls.http.base_url,
            "name": "WiFi Led Studio",
            "version": PROJECT_VERSION,
            "developer_mode": self._wls.config["dev_mode"],
        }

        return web.json_response(data=response, status=200)
