import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint

_LOGGER = logging.getLogger(__name__)


class EffectsEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/effects"

    async def get(self) -> web.Response:
        response = {"status": "success", "effects": {}}
        for virtual in self._wls.virtuals.values():
            if virtual.active_effect:
                response["effects"][virtual.id] = {
                    "effect_type": virtual.active_effect.type,
                    "effect_config": virtual.active_effect.config,
                }
        return web.json_response(data=response, status=200)

    async def put(self, request) -> web.Response:
        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)

        action = data.get("action")
        if action is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "action" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if action not in ["clear_all_effects"]:
            response = {
                "status": "failed",
                "reason": f'Hành động không hợp lệ "{action}"',
            }
            return web.json_response(data=response, status=400)

        # Clear all effects on all devices
        if action == "clear_all_effects":
            self._wls.virtuals.clear_all_effects()
            response = {
                "status": "success",
                "payload": {
                    "type": "info",
                    "message": "Đã xóa tất cả các hiệu ứng trên tất cả các đèn",
                },
            }
            return web.json_response(data=response, status=200)
