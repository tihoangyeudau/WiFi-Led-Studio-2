import json
import logging
import socket

import paho.mqtt.client as mqtt
import voluptuous as vol

from wls.color import parse_color
from wls.config import save_config
from wls.consts import PROJECT_VERSION
from wls.effects.audio import AudioInputSource
from wls.events import Event
from wls.integrations import Integration

_LOGGER = logging.getLogger(__name__)


def extract_ip():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(("10.255.255.255", 1))
        IP = st.getsockname()[0]
    except Exception:
        IP = "127.0.0.1"
    finally:
        st.close()
    return IP


class MQTT_HASS(Integration):
    """MQTT HomeAssistant Integration"""

    NAME = "Home Assistant MQTT"
    DESCRIPTION = "MQTT Integration for Home Assistant"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "name",
                description="Name of this HomeAssistant instance",
                default="Home Assistant",
            ): str,
            vol.Required(
                "topic",
                description="HomeAssistant's discovery prefix",
                default="homeassistant",
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
            vol.Optional(
                "description",
                description="Internal Description",
                default="MQTT Integration with auto-discovery",
            ): str,
        }
    )

    TRANSITION_MAPPING = {
        "wlstransitiontype": "transition_mode",
        "wlstransitiontime": "transition_time",
    }

    def __init__(self, wls, config, active, data):
        super().__init__(wls, config, active, data)

        self._wls = wls
        self._config = config
        self._client = None
        self._data = []
        self._listeners = []

    def publish_virtual_config(self, virtual_id, client):
        virtual = self._wls.virtuals.get(virtual_id)
        client.publish(
            f"{self._config['topic']}/light/{virtual_id}/meta",
            json.dumps(virtual.config),
        )

    def publish_virtual_paused(self, virtual_id, client):
        virtual = self._wls.virtuals.get(virtual_id)
        paused_state = "OFF"
        if virtual.active:
            paused_state = "ON"
        client.publish(
            f"{self._config['topic']}/light/{virtual_id}/state",
            json.dumps({"state": paused_state}),
        )

    def publish_audio_input_changed(self, client, event):
        client.publish(
            f"{self._config['topic']}/select/wlsaudio/state",
            event.audio_input_device_name,
        )

    def on_connect(self, client, userdata, flags, rc):
        total_pixels = 0
        for device in self._wls.devices.values():
            total_pixels += device.pixel_count
        active_pixels = 0
        for virtual in self._wls.virtuals.values():
            if virtual.active:
                active_pixels += virtual.pixel_count
        _LOGGER.info(
            "active_pixels/total_pixels:"
            + str(active_pixels)
            + "/"
            + str(total_pixels)
        )
        # ToDo create sensor with total_pixels

        # Internal State-Handler
        client.subscribe("wls/state")

        # Events
        def publish_scene_actived(event):
            client.publish(
                f"{self._config['topic']}/select/wlssceneselect/state",
                event.scene_id,
            )

        def publish_global_paused_state(event):
            paused_state = "OFF"
            if self._wls.virtuals._paused:
                paused_state = "OFF"
            else:
                paused_state = "ON"
            client.publish(
                f"{self._config['topic']}/switch/wlsplay/state",
                paused_state,
            )

        def publish_single_color_updated(event):
            color = parse_color(event.effect_config.get("color"))
            client.publish(
                f"{self._config['topic']}/light/{event.virtual_id}/state",
                json.dumps(
                    {
                        "state": "on",
                        "color": [color.red, color.green, color.blue],
                        "effect": event.effect_config.get("color"),
                    }
                ),
            )

        def publish_paused_state(event):
            virtual = self._wls.virtuals.get(event.virtual_id)
            paused_state = "OFF"
            if virtual.active:
                paused_state = "ON"
            client.publish(
                f"{self._config['topic']}/light/{event.virtual_id}/state",
                json.dumps({"state": paused_state}),
            )

        self._listeners.append(
            self._wls.events.add_listener(
                publish_scene_actived,
                Event.SCENE_ACTIVATED,
            )
        )

        self._listeners.append(
            self._wls.events.add_listener(
                publish_single_color_updated,
                Event.EFFECT_SET,
                event_filter={"effect_name": "Single Color"},
            )
        )

        self._listeners.append(
            self._wls.events.add_listener(
                lambda event: self.publish_virtual_config(
                    event.virtual_id, client
                ),
                Event.VIRTUAL_CONFIG_UPDATE,
            )
        )

        self._listeners.append(
            self._wls.events.add_listener(
                publish_global_paused_state, Event.GLOBAL_PAUSE
            )
        )

        self._listeners.append(
            self._wls.events.add_listener(
                publish_paused_state, Event.VIRTUAL_PAUSE
            )
        )

        self._listeners.append(
            self._wls.events.add_listener(
                lambda event: self.publish_audio_input_changed(client, event),
                Event.AUDIO_INPUT_DEVICE_CHANGED,
            )
        )

        # HomeAssistant Device Entity
        hass_device = {
            "identifiers": ["yzlights"],
            "configuration_url": f"http://{extract_ip()}:{self._wls.port}/#/Integrations",
            "name": "Wls",
            "model": "BladeMOD",
            "manufacturer": "Yeon",
            "sw_version": f"{PROJECT_VERSION}",
        }

        # SENSOR
        client.subscribe(
            f"{self._config['topic']}/sensor/wlspixelsensor/set"
        )
        client.publish(
            f"{self._config['topic']}/sensor/wlspixelsensor/config",
            json.dumps(
                {
                    "~": f"{self._config['topic']}/sensor/wlspixelsensor",
                    "name": "Used Pixels",
                    "unique_id": "wlspixelsensor",
                    "entity_category": "diagnostic",
                    "cmd_t": "~/set",
                    "stat_t": "~/state",
                    "icon": "mdi:led-variant-outline",
                    "device": hass_device,
                }
            ),
        )

        # SCENE SELECTOR
        client.subscribe(
            f"{self._config['topic']}/select/wlssceneselect/set"
        )
        client.publish(
            f"{self._config['topic']}/select/wlssceneselect/config",
            json.dumps(
                {
                    "~": f"{self._config['topic']}/select/wlssceneselect",
                    "name": "Scene Selector",
                    "unique_id": "wlssceneselect",
                    "cmd_t": "~/set",
                    "stat_t": "~/state",
                    "icon": "mdi:image-multiple-outline",
                    "options": list(self._wls.scenes._scenes.keys()),
                    "entity_category": "config",
                    "device": hass_device,
                }
            ),
        )

        # AUDIO SELECTOR
        client.subscribe(f"{self._config['topic']}/select/wlsaudio/set")
        client.publish(
            f"{self._config['topic']}/select/wlsaudio/config",
            json.dumps(
                {
                    "~": f"{self._config['topic']}/select/wlsaudio",
                    "name": "Audio Selector",
                    "unique_id": "wlsaudio",
                    "cmd_t": "~/set",
                    "stat_t": "~/state",
                    "icon": "mdi:volume-high",
                    "entity_category": "diagnostic",
                    "options": [*AudioInputSource.input_devices().values()],
                    "entity_category": "config",
                    "device": hass_device,
                }
            ),
        )

        # TRANSITION TYPE
        client.subscribe(
            f"{self._config['topic']}/select/wlstransitiontype/set"
        )
        client.publish(
            f"{self._config['topic']}/select/wlstransitiontype/config",
            json.dumps(
                {
                    "~": f"{self._config['topic']}/select/wlstransitiontype",
                    "name": "Transition Type",
                    "unique_id": "wlstransitiontype",
                    "cmd_t": "~/set",
                    "stat_t": "~/state",
                    "icon": "mdi:transfer-right",
                    "entity_category": "config",
                    "options": list(
                        [
                            "Thêm",
                            "Tan biến",
                            "Đẩy",
                            "Trượt",
                            "Mống mắt",
                            "Xuyên qua màu trắng",
                            "Xuyên qua màu đen",
                            "None",
                        ]
                    ),
                    "device": hass_device,
                }
            ),
        )

        # TRANSITION TIME
        client.subscribe(
            f"{self._config['topic']}/number/wlstransitiontime/set"
        )
        client.publish(
            f"{self._config['topic']}/number/wlstransitiontime/config",
            json.dumps(
                {
                    "~": f"{self._config['topic']}/number/wlstransitiontime",
                    "name": "Transition_Time",
                    "unique_id": "wlstransitiontime",
                    "cmd_t": "~/set",
                    "stat_t": "~/state",
                    "icon": "mdi:camera-timer",
                    "min": 0,
                    "max": 5,
                    "step": 0.1,
                    "unit_of_measurement": "s",
                    "entity_category": "config",
                    "device": hass_device,
                }
            ),
        )

        # SWITCH
        client.subscribe(f"{self._config['topic']}/switch/wlsplay/set")
        client.publish(
            f"{self._config['topic']}/switch/wlsplay/config",
            json.dumps(
                {
                    "~": f"{self._config['topic']}/switch/wlsplay",
                    "name": "Play / Pause",
                    "unique_id": "wlsplay",
                    "cmd_t": "~/set",
                    "stat_t": "~/state",
                    "icon": "mdi:play-pause",
                    "device": hass_device,
                }
            ),
        )

        command_template = """{
    "state": "on"
    {%- if red is defined and green is defined and blue is defined -%}
    , "color": [{{ red }}, {{ green }}, {{ blue }}]
    {%- endif -%}
    {%- if effect is defined -%}
    , "effect": "{{ effect }}"
    {%- endif -%}
}
"""

        # Create Virtuals as Light in HomeAssistant
        for virtual in self._wls.virtuals.values():
            if virtual.config["icon_name"].startswith("mdi:"):
                icon = virtual.config["icon_name"]
            else:
                icon = "mdi:led-strip"
            client.publish(
                f"{self._config['topic']}/light/{virtual.id}/config",
                json.dumps(
                    {
                        "~": f"{self._config['topic']}/light/{virtual.id}",
                        "name": "⮑ " + virtual.config["name"],
                        "unique_id": virtual.id,
                        "cmd_t": "~/set",
                        "stat_t": "~/state",
                        "state_template": "{{ value_json.state | lower }}",
                        "state_value_template": "{{ value_json.state | lower }}",
                        "schema": "template",
                        "brightness": False,
                        "enabled_by_default": True,
                        "command_on_template": command_template,
                        "command_off_template": '{"state": "off"}',
                        "red_template": "{{ value_json.color[0] }}",
                        "green_template": "{{ value_json.color[1] }}",
                        "blue_template": "{{ value_json.color[2] }}",
                        "effect_template": "{{ value_json.effect }}",
                        "json_attributes_topic": "~/meta",
                        "icon": icon,
                        "effect": True,
                        # "effect_list": list(COLORS.keys()),
                        # "effect_list": list(self._wls.effects.keys()),
                        "device": hass_device,
                    }
                ),
            )

            client.subscribe(f"{self._config['topic']}/light/{virtual.id}/set")
        client.publish("wls/state", "HomeAssistant initialized")

    def on_message(self, client, userdata, msg):
        _LOGGER.info(
            "MQTT-Message incoming: \n[MQTT    ] Topic: "
            + msg.topic
            + "\n[MQTT    ] Payload: "
            + str(msg.payload)
        )
        segs = msg.topic.split("/")
        try:
            payload = json.loads(msg.payload)
        except json.decoder.JSONDecodeError:
            payload = msg.payload.decode("utf-8")

        paused_state = "OFF"
        if self._wls.virtuals._paused:
            paused_state = "OFF"
        else:
            paused_state = "ON"

        # React to Internal State-Handler
        total_pixels = 0
        for device in self._wls.devices.values():
            total_pixels += device.pixel_count
        active_pixels = 0
        for virtual in self._wls.virtuals.values():
            if virtual.active:
                active_pixels += virtual.pixel_count
        if segs[0] == "wls":
            if payload == "HomeAssistant initialized":
                virtual = self._wls.virtuals.get(
                    next(iter(self._wls.virtuals))
                )
                client.publish(
                    f"{self._config['topic']}/select/wlstransitiontype/state",
                    virtual.config["transition_mode"],
                )
                client.publish(
                    f"{self._config['topic']}/number/wlstransitiontime/state",
                    virtual.config["transition_time"],
                )
                # PausedState
                client.publish(
                    f"{self._config['topic']}/switch/wlsplay/state",
                    paused_state,
                )
                # AudioSelector
                client.publish(
                    f"{self._config['topic']}/select/wlsaudio/state",
                    AudioInputSource.input_devices()[
                        self._wls.config.get("audio", {}).get(
                            "audio_device", {}
                        )
                    ],
                )
                # Pixel-Sensor
                client.publish(
                    f"{self._config['topic']}/sensor/wlspixelsensor/state",
                    str(active_pixels) + " / " + str(total_pixels),
                )
                # publish all virtual data on connect (meta)
                for virtual in self._wls.virtuals.values():
                    self.publish_virtual_config(virtual.id, client)
                    self.publish_virtual_paused(virtual.id, client)
            return

        # React to SET commands
        if segs[3] != "set":
            return
        virtualid = segs[2]

        # React to Global-PlayPause
        if virtualid == "wlsplay":
            # _LOGGER.info("Paused: " + str(self._wls.virtuals._paused) + str(payload))
            self._wls.virtuals.pause_all()
            paused_state = "OFF"
            if self._wls.virtuals._paused:
                paused_state = "OFF"
            else:
                paused_state = "ON"
            client.publish(
                f"{self._config['topic']}/switch/{virtualid}/state",
                paused_state,
            )
            return

        # React to Transition-Type
        if virtualid in self.TRANSITION_MAPPING.keys():
            # _LOGGER.info("Transitions: " + str(payload))
            prior_state = self._wls.config["global_transitions"]
            self._wls.config["global_transitions"] = True
            virtual = self._wls.virtuals.get(
                next(iter(self._wls.virtuals))
            )
            key = self.TRANSITION_MAPPING[virtualid]
            if key == "transition_time":
                try:
                    val = float(payload)
                except ValueError as e:
                    _LOGGER.warning(e)
                    val = 0.5
            else:
                val = payload

            virtual.update_config({key: val})
            self._wls.config["global_transitions"] = prior_state

        # React to Scene-Selector
        elif virtualid == "wlssceneselect":
            self._wls.scenes.activate(payload)

        # React to Audio-Selector
        elif virtualid == "wlsaudio":
            _LOGGER.info("AUDIO DEVICE BROOOO: " + str(payload))
            if hasattr(self._wls, "audio") and self._wls.audio is not None:
                # index = self._wls.audio.get_device_index_by_name(payload)
                index = -1
                for key, value in AudioInputSource.input_devices().items():
                    if str(payload) == value:
                        index = key

                new_config = self._wls.config.get("audio", {})
                new_config["audio_device"] = int(index)
                self._wls.config["audio"] = new_config
                save_config(
                    config=self._wls.config,
                    config_dir=self._wls.config_dir,
                )
                self._wls.audio.update_config(new_config)
            return

        # React to Virtuals
        elif isinstance(payload, dict):
            virtual = self._wls.virtuals.get(virtualid, None)
            if virtual:
                # SET VIRTUAL COLOR AND ACTIVE
                color = payload.get("effect", "orange")
                color = payload.get("color", None)

                if color is not None:
                    effect = self._wls.effects.create(
                        wls=self._wls,
                        type="singleColor",
                        config={"color": color},
                    )
                else:
                    effect = self._wls.effects.create(
                        wls=self._wls,
                        type="singleColor",
                        config={"color": color},
                    )
                try:
                    virtual.set_effect(effect)
                    virtual.active = payload["state"] == "on"
                except (ValueError, RuntimeError) as msg:
                    _LOGGER.warning(msg)

                # Save to config
                for idx, item in enumerate(self._wls.config["virtuals"]):
                    if item["id"] == virtual.id:
                        item["active"] = virtual.active
                        item["effect"] = {}
                        item["effect"]["type"] = "singleColor"
                        item["effect"]["config"] = {"color": color}
                        self._wls.config["virtuals"][idx] = item
                        break

                save_config(
                    config=self._wls.config,
                    config_dir=self._wls.config_dir,
                )

        # client.publish(
        #     f"{self._config['topic']}/light/{virtualid}/state",
        #     msg.payload,
        # )

    # Clean up HomeAssistant
    async def on_delete(self):
        self._client.publish(
            f"{self._config['topic']}/light/wlsscene/config", json.dumps({})
        )
        self._client.publish(
            f"{self._config['topic']}/light/wlstransition/config",
            json.dumps({}),
        )
        self._client.publish(
            f"{self._config['topic']}/select/wlsaudio/config", json.dumps({})
        )
        self._client.publish(
            f"{self._config['topic']}/select/wlssceneselect/config",
            json.dumps({}),
        )
        self._client.publish(
            f"{self._config['topic']}/select/wlstransitiontype/config",
            json.dumps({}),
        )
        self._client.publish(
            f"{self._config['topic']}/number/wlstransitiontime/config",
            json.dumps({}),
        )
        self._client.publish(
            f"{self._config['topic']}/sensor/wlspixelsensor/config",
            json.dumps({}),
        )
        self._client.publish(
            f"{self._config['topic']}/switch/wlsplay/config", json.dumps({})
        )
        for virtual in self._wls.virtuals.values():
            self._client.publish(
                f"{self._config['topic']}/light/{virtual.id}/config",
                json.dumps({}),
            )

    async def on_disconnect(self):
        for remove_listener in self._listeners:
            remove_listener()
        self._listeners = []

    async def connect(self):
        client = mqtt.Client()
        client.on_connect = self.on_connect
        client.on_message = self.on_message
        self._client = client
        if self._config["username"] is not None:
            client.username_pw_set(
                self._config["username"], password=self._config["password"]
            )
        client.connect_async(
            self._config["ip_address"], self._config["port"], 60
        )
        client.loop_start()
