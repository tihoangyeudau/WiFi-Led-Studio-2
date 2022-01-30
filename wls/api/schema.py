import logging
from json import JSONDecodeError

from aiohttp import web

from wls.api import RestEndpoint
from wls.api.utils import PERMITTED_KEYS, convertToJsonSchema
from wls.config import CORE_CONFIG_SCHEMA, RML_CONFIG_SCHEMA
from wls.effects.audio import AudioInputSource
from wls.effects.melbank import Melbanks

_LOGGER = logging.getLogger(__name__)


class SchemaEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/schema"

    VALID_SCHEMAS = {
        "devices",
        "effects",
        "integrations",
        "virtuals",
        "audio",
        "melbanks",
        "rml_preferences",
        "core",
    }

    async def get(self, request) -> web.Response:
        """
        Get wls schemas.
        You may ask for a specific schema/schemas in the request body
        eg. "audio" will return audio schema
        eg. ["audio", "melbanks"] will return audio and melbanks schema
        """
        schemas = set()
        response = {}

        if request.can_read_body:
            try:
                wanted_schemas = await request.json()
            except JSONDecodeError:
                response = {
                    "status": "failed",
                    "reason": "Không giải mã được JSON",
                }
                return web.json_response(data=response, status=400)

            if isinstance(wanted_schemas, list):
                schemas.update(wanted_schemas)
            elif isinstance(wanted_schemas, str):
                schemas.add(wanted_schemas)

            schemas = schemas & self.VALID_SCHEMAS

        # if no schemas left after filtering, or none requested, send them all
        if not schemas:
            schemas = self.VALID_SCHEMAS

        for schema in schemas:
            if schema == "devices":
                response["devices"] = {}
                # Generate all the device schema
                for (
                    device_type,
                    device,
                ) in self._wls.devices.classes().items():
                    response["devices"][device_type] = {
                        "schema": convertToJsonSchema(device.schema()),
                        "id": device_type,
                    }

            elif schema == "effects":
                response["effects"] = {}
                # Generate all the effect schema
                for (
                    effect_type,
                    effect,
                ) in self._wls.effects.classes().items():
                    response["effects"][effect_type] = {
                        "schema": convertToJsonSchema(effect.schema()),
                        "id": effect_type,
                        "name": effect.NAME,
                        "category": effect.CATEGORY,
                    }

            elif schema == "integrations":
                # Generate all the integrations schema
                response["integrations"] = {}
                for (
                    integration_type,
                    integration,
                ) in self._wls.integrations.classes().items():
                    response["integrations"][integration_type] = {
                        "schema": convertToJsonSchema(integration.schema()),
                        "id": integration_type,
                        "name": integration.NAME,
                        "description": integration.DESCRIPTION,
                    }

            elif schema == "virtuals":
                # Get virtuals schema
                response["virtuals"] = {
                    "schema": convertToJsonSchema(
                        self._wls.virtuals.schema()
                    ),
                }

            elif schema == "audio":
                # Get audio schema
                response["audio"] = {
                    "schema": {
                        **convertToJsonSchema(
                            AudioInputSource.AUDIO_CONFIG_SCHEMA.fget(),
                        ),
                        **{"permitted_keys": PERMITTED_KEYS["audio"]},
                    }
                    # | { "properties": {
                    #     "audio_device": {
                    #         "enum": {
                    #             "1337": "Blade-WebAudio"
                    #         }
                    #     }
                    # } }
                    ,
                }

            elif schema == "melbanks":
                # Get melbanks schema
                response["melbanks"] = {
                    "schema": {
                        **convertToJsonSchema(
                            Melbanks.CONFIG_SCHEMA,
                        ),
                        **{"permitted_keys": PERMITTED_KEYS["melbanks"]},
                    },
                }

            elif schema == "rml_preferences":
                # Get rml schema
                response["rml_preferences"] = {
                    "schema": {
                        **convertToJsonSchema(
                            RML_CONFIG_SCHEMA,
                        ),
                        **{
                            "permitted_keys": PERMITTED_KEYS[
                                "rml_preferences"
                            ]
                        },
                    },
                }

            elif schema == "core":
                # Get core config schema
                response["core"] = {
                    "schema": {
                        **convertToJsonSchema(CORE_CONFIG_SCHEMA),
                        **{"permitted_keys": PERMITTED_KEYS["core"]},
                    },
                }

        return web.json_response(data=response, status=200)
