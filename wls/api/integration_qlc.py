import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.config import save_config
from wls.events import Event

_LOGGER = logging.getLogger(__name__)


class QLCEndpoint(RestEndpoint):
    """REST end-point for querying and managing a QLC integration"""

    ENDPOINT_PATH = "/api/integrations/qlc/{integration_id}"

    async def get(self, integration_id) -> web.Response:
        """Get info from QLC+ integration"""
        integration = self._wls.integrations.get(integration_id)
        if (integration is None) or (integration.type != "qlc"):
            response = {"not found": 404}
            return web.json_response(data=response, status=404)

        response = {}

        # generate dict of {effect_id: effect_name}
        effect_names = []
        for effect_type, effect in self._wls.effects.classes().items():
            effect_names.append(effect.NAME)

        scene_names = []
        for scene in self._wls.config["scenes"]:
            scene_names.append(self._wls.config["scenes"][scene]["name"])

        response["event_types"] = {
            Event.EFFECT_SET: {
                "event_name": "Effect Set",
                "event_filters": {"effect_name": effect_names},
            },
            Event.EFFECT_CLEARED: {
                "event_name": "Effect Cleared",
                "event_filters": {},
            },
            Event.SCENE_SET: {
                "event_name": "Scene Set",
                "event_filters": {"scene_name": scene_names},
            },
        }

        response["qlc_widgets"] = await integration.get_widgets()

        response["qlc_listeners"] = integration.data

        return web.json_response(data=response, status=200)

    async def put(self, integration_id, request) -> web.Response:
        """Toggle a QLC event listener"""
        integration = self._wls.integrations.get(integration_id)
        if (integration is None) or (integration.type != "qlc"):
            response = {"not found": 404}
            return web.json_response(data=response, status=404)

        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        event_type = data.get("event_type")
        event_filter = data.get("event_filter")

        if event_type is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "event_type" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if event_filter is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "event_filter" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if type(event_filter) is not dict:
            response = {
                "status": "failed",
                "reason": f'Bộ lọc không hợp lệ "{event_filter}", nên được từ điển vd. {{ "scene_name" : "my scene" }} ',
            }
            return web.json_response(data=response, status=400)

        # toggle the event listener
        if not integration.toggle_event(event_type, event_filter):
            response = {
                "status": "failed",
                "reason": f"Không thể tìm thấy sự kiện có loại {event_type} và bộ lọc {event_filter}",
            }
            return web.json_response(data=response, status=400)

        # Save the configuration (integration will handle modifying "data")
        for _integration in self._wls.config["integrations"]:
            if _integration["id"] == integration_id:
                _integration["data"] = integration.data
                break
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)

    async def post(self, integration_id, request) -> web.Response:
        """Add a new QLC event listener or update an existing one"""
        integration = self._wls.integrations.get(integration_id)
        if (integration is None) or (integration.type != "qlc"):
            response = {"not found": 404}
            return web.json_response(data=response, status=404)

        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        event_type = data.get("event_type")
        event_filter = data.get("event_filter")
        qlc_payload = data.get("qlc_payload")

        if event_type is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "event_type" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if event_filter is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "event_filter" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if type(event_filter) is not dict:
            response = {
                "status": "failed",
                "reason": f'Bộ lọc không hợp lệ "{event_filter}", nên được từ điển vd. {{ "scene_name" : "my scene" }} ',
            }
            return web.json_response(data=response, status=400)

        if qlc_payload is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "qlc_payload" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        # Create a link between wls event and sending the payload
        integration.create_event(event_type, event_filter, True, qlc_payload)

        # Update and save the configuration
        for _integration in self._wls.config["integrations"]:
            if _integration["id"] == integration_id:
                _integration["data"] = integration.data
                break
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)

    async def delete(self, integration_id, request) -> web.Response:
        """Delete a QLC event listener"""
        integration = self._wls.integrations.get(integration_id)
        if (integration is None) or (integration.type != "qlc"):
            response = {"not found": 404}
            return web.json_response(data=response, status=404)

        try:
            data = await request.json()
        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        event_type = data.get("event_type")
        event_filter = data.get("event_filter")

        if event_type is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "event_type" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if event_filter is None:
            response = {
                "status": "failed",
                "reason": 'Thuộc tính bắt buộc "event_filter" không được cung cấp',
            }
            return web.json_response(data=response, status=400)

        if type(event_filter) is not dict:
            response = {
                "status": "failed",
                "reason": f'Bộ lọc không hợp lệ "{event_filter}", nên được từ điển vd. {{ "scene_name" : "my scene" }} ',
            }
            return web.json_response(data=response, status=400)

        # Delete the listener and event from data
        integration.delete_event(event_type, event_filter)

        # Save the configuration (integration will handle modifying "data")
        for _integration in self._wls.config["integrations"]:
            if _integration["id"] == integration_id:
                _integration["data"] = integration.data
                break
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {"status": "success"}
        return web.json_response(data=response, status=200)
