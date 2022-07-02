import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.config import save_config
from wls.events import SceneActivatedEvent
from wls.utils import generate_id

_LOGGER = logging.getLogger(__name__)


class ScenesEndpoint(RestEndpoint):
    """REST end-point for querying and managing scenes"""

    ENDPOINT_PATH = "/api/scenes"

    async def get(self) -> web.Response:
        """Get all scenes"""
        response = {
            "status": "success",
            "scenes": self._wls.config["scenes"],
        }
        return web.json_response(data=response, status=200)

    async def delete(self, request) -> web.Response:
        """Delete a scene"""
        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)

        scene_id = data.get("id")
        if scene_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "scene_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if scene_id not in self._wls.config["scenes"].keys():
            response = {
                "status": "failed",
                "reason": f"Cảnh {scene_id} không tồn tại",
            }
            return web.json_response(data=response, status=400)

        # Delete the scene from configuration
        del self._wls.config["scenes"][scene_id]

        # Save the config
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)

    async def put(self, request) -> web.Response:
        """Activate a scene"""
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

        if action not in ["activate", "activate_in", "deactivate", "rename"]:
            response = {
                "status": "failed",
                "reason": f'Hành động không hợp lệ "{action}"',
            }
            return web.json_response(data=response, status=400)

        scene_id = data.get("id")
        if scene_id is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "scene_id" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if scene_id not in self._wls.config["scenes"].keys():
            response = {
                "status": "failed",
                "reason": f'Cảnh "{scene_id}" không tồn tại',
            }
            return web.json_response(data=response, status=400)

        scene = self._wls.config["scenes"][scene_id]

        if action == "activate_in":
            ms = data.get("ms")
            if ms is None:
                response = {
                    "status": "failed",
                    "reason": 'Required attribute "ms" was not provided',
                }
                return web.json_response(data=response, status=400)
            self._wls.loop.call_later(
                ms, self._wls.scenes.activate, scene_id
            )
            response = {
                "status": "success",
                "payload": {
                    "type": "info",
                    "message": f"Activated scene {scene['name']}",
                },
            }
            return web.json_response(data=response, status=200)

        if action == "activate":
            for virtual in self._wls.virtuals.values():
                # Check virtual is in scene, make no changes if it isn't
                if virtual.id not in scene["virtuals"].keys():
                    # _LOGGER.info(
                    #     ("virtual with id {} has no data in scene {}").format(
                    #         virtual.id, scene_id
                    #     )
                    # )
                    continue

                # Set effect of virtual to that saved in the scene,
                # clear active effect of virtual if no effect in scene
                if scene["virtuals"][virtual.id]:
                    # Create the effect and add it to the virtual
                    effect = self._wls.effects.create(
                        wls=self._wls,
                        type=scene["virtuals"][virtual.id]["type"],
                        config=scene["virtuals"][virtual.id]["config"],
                    )
                    virtual.set_effect(effect)
                else:
                    virtual.clear_effect()

            self._wls.events.fire_event(SceneActivatedEvent(scene_id))
            response = {
                "status": "success",
                "payload": {
                    "type": "info",
                    "message": f"Đã kích hoạt cảnh {scene['name']}",
                },
            }

        elif action == "deactivate":
            for virtual in self._wls.virtuals.values():
                # Check virtual is in scene, make no changes if it isn't
                if virtual.id not in scene["virtuals"].keys():
                    _LOGGER.info(
                        ("Đèn với id {} không có dữ liệu trong cảnh {}").format(
                            virtual.id, scene_id
                        )
                    )
                    continue

                # Clear the effect of virtual,
                if scene["virtuals"][virtual.id]:
                    virtual.clear_effect()

            response = {
                "status": "success",
                "payload": {
                    "type": "info",
                    "message": f"Bỏ kích hoạt cảnh {scene['name']}",
                },
            }

        elif action == "rename":
            name = data.get("name")
            if name is None:
                response = {
                    "status": "failed",
                    "reason": 'Thuộc tính bắt buộc "name" không được cung cấp',
                }
                return web.json_response(data=response, status=400)

            # Update and save config
            self._wls.config["scenes"][scene_id]["name"] = name
            save_config(
                config=self._wls.config,
                config_dir=self._wls.config_dir,
            )

            response = {
                "status": "success",
                "payload": {
                    "type": "info",
                    "message": f"Đã đổi tên cảnh thành {name}",
                },
            }
        return web.json_response(data=response, status=200)

    async def post(self, request) -> web.Response:
        """Save current effects of virtuals as a scene"""
        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)

        scene_name = data.get("name")
        scene_image = data.get("scene_image")
        if scene_image is None:
            scene_image = "Wallpaper"
        if scene_name is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "scene_name" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        scene_id = generate_id(scene_name)

        scene_config = {}
        scene_config["name"] = scene_name
        scene_config["virtuals"] = {}
        scene_config["scene_image"] = scene_image
        for virtual in self._wls.virtuals.values():
            effect = {}
            if virtual.active_effect:
                effect["type"] = virtual.active_effect.type
                effect["config"] = virtual.active_effect.config
                # effect['name'] = virtual.active_effect.name
            scene_config["virtuals"][virtual.id] = effect

        # Update the scene if it already exists, else create it
        self._wls.config["scenes"][scene_id] = scene_config

        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {
            "status": "success",
            "scene": {"id": scene_id, "config": scene_config},
        }
        return web.json_response(data=response, status=200)
