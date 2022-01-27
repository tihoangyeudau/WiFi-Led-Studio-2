import logging

import paho.mqtt.client as mqtt
import voluptuous as vol

from wls.events import SceneActivatedEvent

# from wls.events import Event
from wls.integrations import Integration

_LOGGER = logging.getLogger(__name__)


class MQTT(Integration):
    """MQTT Integration"""

    NAME = "MQTT"
    DESCRIPTION = "MQTT Integration"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "name",
                description="Name of this integration instance and associated settings",
                default="MQTT",
            ): str,
            vol.Required(
                "topic",
                description="Description of this integration",
                default="",
            ): str,
            vol.Required(
                "ip_address",
                description="MQTT ip address",
                default="127.0.0.1",
            ): str,
            vol.Required(
                "port", description="MQTT port", default=1883
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
            vol.Optional(
                "username",
                description="MQTT username",
                default="",
            ): str,
            vol.Optional(
                "password",
                description="MQTT password",
                default="",
            ): str,
        }
    )

    def __init__(self, wls, config, active, data):
        super().__init__(wls, config, active, data)

        self._wls = wls
        self._config = config
        self._client = None
        self._data = []
        self._listeners = []
        _LOGGER.info(f"CONFIG: {self._config}")

    def on_connect(self, client, userdata, flags, rc):
        _LOGGER.info("Connecting2")
        _LOGGER.info("Connected with result code " + str(rc))

        client.subscribe(f"{self._config['topic']}/#")
        # client.publish(self._config['topic'], "connected")
        client.publish(f"{self._config['topic']}/STAT", "online")
        client.publish(
            f"{self._config['topic']}/SCENES",
            str(self._wls.config["scenes"]),
        )
        client.publish(
            f"{self._config['topic']}/DEVICES",
            str(self._wls.config["virtuals"]),
        )

    def on_message(self, client, userdata, msg):
        _LOGGER.info(msg.topic + " " + str(msg.payload))

        if msg.topic == f"{self._config['topic']}/SCENE":

            scene_id = msg.payload.decode("utf8")
            # SET SCENE not_matt plz do a callable function like set_scene(scene_id)
            if scene_id is None:
                response = {
                    "status": "failed",
                    "reason": 'Required attribute "scene_id" was not provided',
                }
                return _LOGGER.warning(response)
            _LOGGER.warning(str(self._wls.config["scenes"].keys()))
            if scene_id not in self._wls.config["scenes"].keys():
                response = {
                    "status": "failed",
                    "reason": f'Scene "{scene_id}" does not exist',
                }
                return _LOGGER.warning(response)

            scene = self._wls.config["scenes"][scene_id]

            for virtual in self._wls.virtuals.values():
                # Check virtual is in scene, make no changes if it isn't
                if virtual.id not in scene["virtuals"].keys():
                    _LOGGER.info(
                        ("virtual with id {} has no data in scene {}").format(
                            virtual.id, scene_id
                        )
                    )
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

            self._wls.events.fire_event(SceneActivatedEvent(scene["name"]))
            # SET SCENE END

    async def connect(self):
        _LOGGER.info("Connecting1")
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        if self._config["username"] is not None:
            client.username_pw_set(
                self._config["username"], password=self._config["password"]
            )
        client.connect_async(
            self._config["ip_address"], self._config["port"], 60
        )
        client.loop_start()
        _LOGGER.info(client)
