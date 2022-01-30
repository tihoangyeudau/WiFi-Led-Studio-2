# from wls.utils import RegistryLoader, async_fire_and_forget, async_fire_and_return, async_callback
# from wls.events import Event
# import importlib
# import pkgutil
import logging

# import aiohttp
# import asyncio
import voluptuous as vol

from wls.integrations import Integration

# import numpy as np


# import time
# import os
# import re

_LOGGER = logging.getLogger(__name__)


class Spotify(Integration):
    """Spotify Integration"""

    NAME = "Spotify"
    DESCRIPTION = "Kích hoạt các cảnh với Spotify Connect [BETA]. Yêu cầu Spotify Premium."

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "name",
                description="Tên của phiên bản tích hợp này và các cài đặt liên quan",
                default="Spotify",
            ): str,
            vol.Required(
                "description",
                description="Mô tả về sự tích hợp này",
                default="Kích hoạt các cảnh với Spotify",
            ): str,
        }
    )

    def __init__(self, wls, config, active, data):
        super().__init__(wls, config, active, data)

        self._wls = wls
        self._config = config
        self._data = {}

        self.restore_from_data(data)

    def restore_from_data(self, data):
        """Might be used in future"""
        self._data = data

    def get_triggers(self):
        return self._data

    def add_trigger(self, scene_id, song_id, song_name, song_position):
        """Add a trigger to saved triggers"""
        trigger_id = f"{song_id}-{str(song_position)}"
        if scene_id not in self._data.keys():
            self._data[scene_id] = {}
        self._data[scene_id][trigger_id] = [song_id, song_name, song_position]

    def delete_trigger(self, trigger_id):
        """Delete a trigger from saved triggers"""
        for scene_id in self._data.keys():
            if trigger_id in self._data[scene_id].keys():
                del self._data[scene_id][trigger_id]

    async def connect(self):
        super().connect()

    async def disconnect(self):
        super().disconnect()
