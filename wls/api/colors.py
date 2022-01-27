import logging

from aiohttp import web

from wls.api import RestEndpoint
from wls.color import validate_color

_LOGGER = logging.getLogger(__name__)


class ColorEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/colors"

    async def get(self) -> web.Response:
        """
        Get Wls colors and gradients
        """
        response = {
            "colors": dict(
                zip(("builtin", "user"), self._wls.colors.get_all())
            ),
            "gradients": dict(
                zip(("builtin", "user"), self._wls.gradients.get_all())
            ),
        }

        return web.json_response(data=response, status=200)

    async def delete(self, request) -> web.Response:
        """
        Deletes a user defined color or gradient
        Request body is a string of the color key to delete
        eg. ["my_red_color"]
        """

        data = await request.json()

        for key in data:
            del self._wls.colors[key]
            del self._wls.gradients[key]

        response = {
            "status": "success",
            "payload": {
                "type": "success",
                "reason": "Deleted",
            },
        }

        return web.json_response(data=response, status=200)

    async def post(self, request) -> web.Response:
        """
        Creates or updates existing colors or gradients.
        eg. {"my_red_color": "#ffffff"}
        or  {"my_cool_gradient": "lin..."}
        """

        data = await request.json()

        for key, val in data.items():
            try:
                is_color = validate_color(val)
            except ValueError:
                is_color = False
            if is_color:
                self._wls.colors[key] = val
            else:
                self._wls.gradients[key] = val

        response = {
            "status": "success",
            "payload": {
                "type": "success",
                "reason": "Saved",
            },
        }

        return web.json_response(data=response, status=200)
