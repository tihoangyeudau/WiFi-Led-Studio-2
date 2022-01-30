import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.config import save_config
from wls.utils import generate_id

_LOGGER = logging.getLogger(__name__)


class VirtualsEndpoint(RestEndpoint):
    """REST end-point for querying and managing virtuals"""

    ENDPOINT_PATH = "/api/virtuals"

    async def get(self) -> web.Response:
        """
        Get info of all virtuals
        """
        response = {"status": "success", "virtuals": {}}
        response["paused"] = self._wls.virtuals._paused
        for virtual in self._wls.virtuals.values():
            response["virtuals"][virtual.id] = {
                "config": virtual.config,
                "id": virtual.id,
                "is_device": virtual.is_device,
                "segments": virtual.segments,
                "pixel_count": virtual.pixel_count,
                "active": virtual.active,
                "effect": {},
            }
            if virtual.active_effect:
                effect_response = {}
                effect_response["config"] = virtual.active_effect.config
                effect_response["name"] = virtual.active_effect.name
                effect_response["type"] = virtual.active_effect.type
                response["virtuals"][virtual.id]["effect"] = effect_response

        return web.json_response(data=response, status=200)

    async def put(self) -> web.Response:
        """
        Toggle "paused" state of all virtuals
        """
        self._wls.virtuals.pause_all()

        response = {
            "status": "success",
            "paused": self._wls.virtuals._paused,
        }

        return web.json_response(data=response, status=200)

    async def post(self, request) -> web.Response:
        """
        Create a new virtual or update config of an existing one
        """
        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)

        virtual_config = data.get("config")
        if virtual_config is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "config" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        virtual_id = data.get("id")

        # Update virtual config if id exists
        if virtual_id is not None:
            virtual = self._wls.virtuals.get(virtual_id)
            if virtual is None:
                response = {
                    "status": "failed",
                    "reason": f"Đèn ảo có ID {virtual_id} không được tìm thấy",
                }
                return web.json_response(data=response, status=404)
            # Update the virtual's configuration
            virtual.config = virtual_config
            _LOGGER.info(
                f"Đã cập nhật đèn ảo {virtual.id} sang cấu hình {virtual_config}"
            )
            # Update wls's config
            for idx, item in enumerate(self._wls.config["virtuals"]):
                if item["id"] == virtual.id:
                    item["config"] = virtual.config
                    self._wls.config["virtuals"][idx] = item
                    break
        # Or, create new virtual if id không tồn tại
        else:
            virtual_id = generate_id(virtual_config.get("name"))

            # Create the virtual
            _LOGGER.info(f"Đang tạo đèn ảo với cấu hình {virtual_config}")

            virtual = self._wls.virtuals.create(
                id=virtual_id,
                is_device=False,
                config=virtual_config,
                wls=self._wls,
            )

            # Update the configuration
            self._wls.config["virtuals"].append(
                {
                    "id": virtual.id,
                    "config": virtual.config,
                    "is_device": virtual.is_device,
                }
            )

        # Save config
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {
            "status": "success",
            "virtual": {
                "config": virtual.config,
                "id": virtual.id,
                "is_device": virtual.is_device,
            },
        }
        return web.json_response(data=response, status=200)
