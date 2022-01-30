import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.config import save_config
from wls.utils import generate_id

_LOGGER = logging.getLogger(__name__)


class VirtualPresetsEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/virtuals/{virtual_id}/presets"

    async def get(self, virtual_id) -> web.Response:
        """
        Get presets for active effect of a virtual
        """
        virtual = self._wls.virtuals.get(virtual_id)
        if virtual is None:
            response = {
                "status": "failed",
                "reason": f"Đèn ảo có ID {virtual_id} không được tìm thấy",
            }
            return web.json_response(data=response, status=404)

        if not virtual.active_effect:
            response = {
                "status": "failed",
                "reason": f"Đèn ảo {virtual_id} không kích hoạt hiệu ứng nào",
            }
            return web.json_response(data=response, status=400)

        effect_id = virtual.active_effect.type

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
            "virtual": virtual_id,
            "effect": effect_id,
            "default_presets": default,
            "custom_presets": custom,
        }

        return web.json_response(data=response, status=200)

    async def put(self, virtual_id, request) -> web.Response:
        """Set active effect of virtual to a preset"""
        virtual = self._wls.virtuals.get(virtual_id)
        if virtual is None:
            response = {
                "status": "failed",
                "reason": f"Đèn ảo có ID {virtual_id} không được tìm thấy",
            }
            return web.json_response(data=response, status=404)

        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        category = data.get("category")
        effect_id = data.get("effect_id")
        preset_id = data.get("preset_id")

        if category is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "category" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if category not in ["default_presets", "custom_presets"]:
            response = {
                "status": "failed",
                "reason": f'Loại {category} không là "wls_presets" hoặc "user_presets"',
            }
            return web.json_response(data=response, status=400)

        if category == "default_presets":
            category = "wls_presets"
        else:
            category = "user_presets"

        if effect_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "effect_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if effect_id not in self._wls.config[category].keys():
            response = {
                "status": "failed",
                "reason": f"Hiệu ứng {effect_id} không tồn tại trong loại {category}",
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

        # Create the effect and add it to the virtual
        effect_config = self._wls.config[category][effect_id][preset_id][
            "config"
        ]
        effect = self._wls.effects.create(
            wls=self._wls, type=effect_id, config=effect_config
        )
        try:
            virtual.set_effect(effect)
        except (ValueError, RuntimeError) as msg:
            response = {
                "status": "failed",
                "payload": {"type": "warning", "reason": str(msg)},
            }
            return web.json_response(data=response, status=202)

        # Update and save the configuration
        for virtual in self._wls.config["virtuals"]:
            if virtual["id"] == virtual_id:
                # if not ('effect' in virtual):
                virtual["effect"] = {}
                virtual["effect"]["type"] = effect_id
                virtual["effect"]["config"] = effect_config
                break
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        effect_response = {}
        effect_response["config"] = effect.config
        effect_response["name"] = effect.name
        effect_response["type"] = effect.type

        response = {"status": "success", "effect": effect_response}
        return web.json_response(data=response, status=200)

    async def post(self, virtual_id, request) -> web.Response:
        """save configuration of active virtual effect as a custom preset"""
        virtual = self._wls.virtuals.get(virtual_id)
        if virtual is None:
            response = {
                "status": "failed",
                "reason": f"Đèn ảo có ID {virtual_id} không được tìm thấy",
            }
            return web.json_response(data=response, status=404)

        if not virtual.active_effect:
            response = {
                "status": "failed",
                "reason": f"Đèn ảo {virtual_id} không kích hoạt hiệu ứng nào",
            }
            return web.json_response(data=response, status=404)

        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        preset_name = data.get("name")
        if preset_name is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "preset_name" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        preset_id = generate_id(preset_name)
        effect_id = virtual.active_effect.type

        # If no presets for the effect, create a dict to store them
        if effect_id not in self._wls.config["user_presets"].keys():
            self._wls.config["user_presets"][effect_id] = {}

        # Update the preset if it already exists, else create it
        self._wls.config["user_presets"][effect_id][preset_id] = {}
        self._wls.config["user_presets"][effect_id][preset_id][
            "name"
        ] = preset_name
        self._wls.config["user_presets"][effect_id][preset_id][
            "config"
        ] = virtual.active_effect.config

        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {
            "status": "success",
            "preset": {
                "id": preset_id,
                "name": preset_name,
                "config": virtual.active_effect.config,
            },
        }
        return web.json_response(data=response, status=200)

    async def delete(self, virtual_id) -> web.Response:
        """clear effect of a virtual"""
        virtual = self._wls.virtuals.get(virtual_id)
        if virtual is None:
            response = {
                "status": "failed",
                "reason": f"Đèn ảo có ID {virtual_id} không được tìm thấy",
            }
            return web.json_response(data=response, status=404)

        # Clear the effect
        virtual.clear_effect()

        for virtual in self._wls.config["virtuals"]:
            if virtual["id"] == virtual_id:
                if "effect" in virtual:
                    del virtual["effect"]
                    break
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success", "effect": {}}
        return web.json_response(data=response, status=200)
