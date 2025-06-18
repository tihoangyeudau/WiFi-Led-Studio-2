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
            return await self.json_decode_error()

        action = data.get("action")
        if action is None:
            return await self.invalid_request('Thuộc tính bắt buộc "action" không được cung cấp')

        if action not in ["clear_all_effects", "toggle_led_state"]:
            return await self.invalid_request(f'Hành động không hợp lệ "{action}"')

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

        # Toggle LED state
        elif action == "toggle_led_state":
            try:
                self._wls.toggle_led_state()
                response = {
                    "status": "success",
                    "payload": {
                        "type": "info",
                        "message": "Đã chuyển đổi trạng thái LED",
                    },
                }
                return web.json_response(data=response, status=200)
            except Exception as e:
                _LOGGER.error(f"Lỗi khi toggle LED state: {e}")
                return await self.invalid_request(f"Không thể chuyển đổi trạng thái LED: {str(e)}")
