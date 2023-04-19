import logging
from json import JSONDecodeError

import voluptuous as vol
from aiohttp import web

from wls.api import RestEndpoint
from wls.api.utils import PERMITTED_KEYS
from wls.config import CORE_CONFIG_SCHEMA, RML_CONFIG_SCHEMA, save_config
from wls.effects.audio import AudioInputSource
from wls.effects.melbank import Melbanks

_LOGGER = logging.getLogger(__name__)

CORE_CONFIG_KEYS = set(map(str, CORE_CONFIG_SCHEMA.schema.keys()))


def validate_and_trim_config(config, schema, node):
    for key in config.keys():
        if key not in PERMITTED_KEYS[node]:
            raise KeyError(f"Không xác định/bị cấm {node} khóa cấu hình: '{key}'")

    validated_config = schema(config)
    return {key: validated_config[key] for key in config.keys()}


class ConfigEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/config"

    async def get(self, request) -> web.Response:
        """
        Get complete wls config.
        You may ask for a specific key/keys in the request body
        eg. "audio" will return audio config
        eg. ["audio", "melbanks"] will return audio and melbanks config
        """
        keys = set()

        if request.can_read_body:
            try:
                wanted_keys = await request.json()
            except JSONDecodeError:
                response = {
                    "status": "failed",
                    "reason": "Không giải mã được JSON",
                }
                return web.json_response(data=response, status=400)

            if isinstance(wanted_keys, list):
                keys.update(wanted_keys)
            elif isinstance(wanted_keys, str):
                keys.add(wanted_keys)

            keys = keys & CORE_CONFIG_KEYS

        # if no keys left after filtering, or none requested, send them all
        if not keys:
            keys = CORE_CONFIG_KEYS

        response = {}
        for key in keys:
            config = self._wls.config.get(key)

            if key == "audio":
                config = AudioInputSource.AUDIO_CONFIG_SCHEMA.fget()(config)
            elif key == "melbanks":
                config = Melbanks.CONFIG_SCHEMA(config)
            elif key == "rml_preferences":
                config = RML_CONFIG_SCHEMA(config)

            response[key] = config

        return web.json_response(data=response, status=200)

    async def delete(self) -> web.Response:
        """
        Resets config to defaults and restarts wls
        """
        self._wls.config = CORE_CONFIG_SCHEMA({})

        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        response = {
            "status": "success",
            "payload": {
                "type": "success",
                "reason": "Đặt lại cấu hình về giá trị mặc định",
            },
        }

        self._wls.loop.call_soon_threadsafe(self._wls.stop, 4)

        return web.json_response(data=response, status=200)

    async def post(self, request) -> web.Response:
        """
        Loads a complete config and restarts wls
        """
        try:
            config = await request.json()

            audio_config = AudioInputSource.AUDIO_CONFIG_SCHEMA.fget()(
                config.pop("audio", {})
            )
            rml_config = RML_CONFIG_SCHEMA(
                config.pop("rml_preferences", {})
            )
            melbanks_config = Melbanks.CONFIG_SCHEMA(
                config.pop("melbanks", {})
            )
            core_config = CORE_CONFIG_SCHEMA(config)

            core_config["audio"] = audio_config
            core_config["rml_preferences"] = rml_config
            core_config["melbanks"] = melbanks_config

            self._wls.config = core_config

            save_config(
                config=self._wls.config,
                config_dir=self._wls.config_dir,
            )

            self._wls.loop.call_soon_threadsafe(self._wls.stop, 4)

            return web.json_response(data={"status": "success"}, status=200)

        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)
        except vol.MultipleInvalid as msg:
            response = {
                "status": "failed",
                "payload": {"type": "warning", "reason": str(msg)},
            }
            return web.json_response(data=response, status=400)

    async def put(self, request) -> web.Response:
        """
        Updates wls config
        """
        try:
            config = await request.json()

            audio_config = validate_and_trim_config(
                config.pop("audio", {}),
                AudioInputSource.AUDIO_CONFIG_SCHEMA.fget(),
                "audio",
            )
            rml_config = validate_and_trim_config(
                config.pop("rml_preferences", {}),
                RML_CONFIG_SCHEMA,
                "rml_preferences",
            )
            melbanks_config = validate_and_trim_config(
                config.pop("melbanks", {}), Melbanks.CONFIG_SCHEMA, "melbanks"
            )
            core_config = validate_and_trim_config(
                config, CORE_CONFIG_SCHEMA, "core"
            )

            self._wls.config["audio"].update(audio_config)
            self._wls.config["melbanks"].update(melbanks_config)
            self._wls.config.update(core_config)

            # handle special case rml_preferences nested dict
            for key in rml_config:
                if key in self._wls.config["rml_preferences"]:
                    self._wls.config["rml_preferences"][key].update(
                        rml_config[key]
                    )
                else:
                    self._wls.config["rml_preferences"][key] = rml_config[
                        key
                    ]

            # TODO
            # Do something if rml preferences config is updated

            if (
                hasattr(self._wls, "audio")
                and self._wls.audio is not None
                and audio_config
            ):
                self._wls.audio.update_config(self._wls.config["audio"])

            if hasattr(self._wls, "audio") and melbanks_config:
                self._wls.audio.melbanks.update_config(
                    self._wls.config["melbanks"]
                )

            if core_config and not (
                any(
                    key in core_config
                    for key in ["global_brightness", "create_segments"]
                )
                and len(core_config) == 1
            ):
                self._wls.loop.call_soon_threadsafe(self._wls.stop, 4)

            save_config(
                config=self._wls.config,
                config_dir=self._wls.config_dir,
            )

            return web.json_response(data={"status": "success"}, status=200)

        except JSONDecodeError:
            response = {
                "status": "failed",
                "reason": "Không giải mã được JSON",
            }
            return web.json_response(data=response, status=400)

        except (KeyError, vol.MultipleInvalid) as msg:
            response = {
                "status": "failed",
                "payload": {"type": "warning", "reason": str(msg)},
            }
            return web.json_response(data=response, status=400)
