import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.config import save_config

_LOGGER = logging.getLogger(__name__)


class PresetsEndpoint(RestEndpoint):
    """REST end-point for querying and managing presets"""

    ENDPOINT_PATH = "/api/effects/{effect_id}/presets"

    async def get(self, effect_id) -> web.Response:
        """Get all presets for an effect"""

        try:
            self._wls.effects.get_class(effect_id)
        except BaseException:
            response = {
                "status": "failed",
                "reason": f"Hiệu ứng {effect_id} không tồn tại",
            }
            return web.json_response(data=response, status=400)

        if effect_id in self._wls.config["wls_presets"].keys():
            default = self._wls.config["wls_presets"][effect_id]
        else:
            default = {}

        if effect_id in self._wls.config["user_presets"].keys():
            custom = self._wls.config["user_presets"][effect_id]
        else:
            custom = {}

        response = {
            "status": "success",
            "effect": effect_id,
            "default_presets": default,
            "custom_presets": custom,
        }
        return web.json_response(data=response, status=200)

    async def put(self, effect_id, request) -> web.Response:
        """Rename a preset"""
        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)

        preset_id = data.get("preset_id")
        category = data.get("category")
        name = data.get("name")

        if category is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "category" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if category not in ["wls_presets", "user_presets"]:
            response = {
                "status": "failed",
                "reason": 'Loại {} không phải là "wls_presets" hoặc "user_presets"'.format(
                    category
                ),
            }
            return web.json_response(data=response, status=400)

        if effect_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "effect_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if effect_id not in self._wls.config[category].keys():
            response = {
                "status": "failed",
                "reason": "Hiệu ứng {} không tồn tại in category {}".format(
                    effect_id, category
                ),
            }
            return web.json_response(data=response, status=400)

        try:
            self._wls.effects.get_class(effect_id)
        except BaseException:
            response = {
                "status": "failed",
                "reason": f"Hiệu ứng {effect_id} không tồn tại",
            }
            return web.json_response(data=response, status=400)

        if preset_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "preset_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if preset_id not in self._wls.config[category][effect_id].keys():
            response = {
                "status": "failed",
                "reason": "Cài trước {} không tồn tại cho hiệu ứng {} trong loại {}".format(
                    preset_id, effect_id, category
                ),
            }
            return web.json_response(data=response, status=400)

        if name is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "name" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        # Update and save config
        self._wls.config[category][effect_id][preset_id]["name"] = name
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)

    async def delete(self, effect_id, request) -> web.Response:
        """Delete a preset"""
        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        preset_id = data.get("preset_id")
        category = data.get("category")

        if category is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "category" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if category not in ["wls_presets", "user_presets"]:
            response = {
                "status": "failed",
                "reason": 'Loại {} không phải là "wls_presets" hoặc "user_presets"'.format(
                    category
                ),
            }
            return web.json_response(data=response, status=400)

        if effect_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "effect_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        try:
            self._wls.effects.get_class(effect_id)
        except BaseException:
            response = {
                "status": "failed",
                "reason": f"Hiệu ứng {effect_id} không tồn tại",
            }
            return web.json_response(data=response, status=400)

        if effect_id not in self._wls.config[category].keys():
            response = {
                "status": "failed",
                "reason": "Hiệu ứng {} không tồn tại trong loại {}".format(
                    effect_id, category
                ),
            }
            return web.json_response(data=response, status=400)

        if preset_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "preset_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if preset_id not in self._wls.config[category][effect_id].keys():
            response = {
                "status": "failed",
                "reason": "Cài trước {} không tồn tại cho hiệu ứng {} trong loại {}".format(
                    preset_id, effect_id, category
                ),
            }
            return web.json_response(data=response, status=400)

        # Delete the preset from configuration
        del self._wls.config[category][effect_id][preset_id]

        # Save the config
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)
