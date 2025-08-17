import logging

import voluptuous as vol

from wls.config import save_config
from wls.events import SceneActivatedEvent, SceneDeletedEvent
from wls.utils import generate_id

_LOGGER = logging.getLogger(__name__)


class Scenes:
    """Scenes manager"""

    # Interfaces directly with config - no real need to create Scene objects.

    def __init__(self, wls):
        self._wls = wls
        self._scenes = self._wls.config["scenes"]

        def virtuals_validator(virtual_ids):
            return list(
                virtual_id
                for virtual_id in virtual_ids
                if self._wls.virtuals.get(virtual_id)
            )

        self.SCENE_SCHEMA = vol.Schema(
            {
                vol.Required("name", description="Tên của cảnh"): str,
                vol.Optional(
                    "scene_image",
                    description="Hình ảnh hoặc biểu tượng để hiển thị",
                    default="Wallpaper",
                ): str,
                vol.Optional(
                    "scene_puturl",
                    description="Khi kích hoạt cảnh, URL cũng là PUT",
                ): str,
                vol.Optional(
                    "scene_payload",
                    description="Khi kích hoạt cảnh, hãy gửi payload này tới scene_puturl",
                ): str,
                vol.Required(
                    "virtuals",
                    description="Hiệu ứng của đèn ảo này sẽ được lưu lại",
                ): virtuals_validator,
            }
        )

    def save_to_config(self):
        self._wls.config["scenes"] = self._scenes
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

    def create_from_config(self, config):
        # maybe use this to sanitise scenes on startup or smth
        pass

    def create(self, scene_config, scene_id=None):
        """Creates a scene of current effects of specified virtuals if no ID given, else updates one with matching id"""
        scene_config = self.SCENE_SCHEMA(scene_config)
        scene_id = (
            scene_id
            if scene_id in self._scenes
            else generate_id(scene_config["name"])
        )

        virtual_effects = {}
        for virtual in scene_config["virtuals"]:
            effect = {}
            if virtual.active_effect and virtual.active_effect.type not in ["dummy", "screen_capture"]:
                effect["type"] = virtual.active_effect.type
                effect["config"] = virtual.active_effect.config
            virtual_effects[virtual.id] = effect
        scene_config["virtuals"] = virtual_effects

        # Update the scene if it already exists, else create it
        self._scenes[scene_id] = scene_config
        self.save_to_config()

    def activate(self, scene_id):
        """Activate a scene"""
        scene = self.get(scene_id)
        if not scene:
            _LOGGER.error(f"Không tìm thấy cảnh có tên: {scene_id}")
            return

        for virtual_id in scene["virtuals"]:
            virtual = self._wls.virtuals.get(virtual_id)
            if not virtual:
                # virtual has been deleted since scene was created
                # remove from scene?
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

    def destroy(self, scene_id):
        """Deletes a scene"""

        if not self._scenes.pop(scene_id, None):
            _LOGGER.error("Không thể xóa cảnh: {scene_id}, nó không tồn tại")
        self._wls.events.fire_event(SceneDeletedEvent(scene_id))
        self.save_to_config()

    def __iter__(self):
        return iter(self._scenes)

    def values(self):
        return self._scenes.values()

    def get(self, *args):
        return self._scenes.get(*args)
