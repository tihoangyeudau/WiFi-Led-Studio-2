import logging

from aiohttp import web

from wls.api import RestEndpoint
from wls.consts import PROJECT_VERSION
from wls.utils import git_version

_LOGGER = logging.getLogger(__name__)


class InfoEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/info"

    async def get(self) -> web.Response:
        GIT_COMMIT_ID = git_version()
        response = {
            "url": self._wls.http.base_url,
            "name": "WiFi Led Studio",
            "version": PROJECT_VERSION,
            "git_build_commit": GIT_COMMIT_ID,
            "developer_mode": self._wls.config["dev_mode"],
        }

        return web.json_response(data=response, status=200)
