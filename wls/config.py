import datetime
import json
import logging
import os
import shutil
import sys

import voluptuous as vol
from pkg_resources import parse_version

from wls.consts import CONFIGURATION_VERSION

CONFIG_DIRECTORY = ".wls"
CONFIG_FILE_NAME = "cauhinh.json"
PRESETS_FILE_NAME = "caitruoc.json"

PRIVATE_KEY_FILE = "privkey.pem"
CHAIN_KEY_FILE = "fullchain.pem"

_default_rml_settings = {
    "rml_preferred_mode": "UDP",
    "realtime_gamma_enabled": False,
    "force_max_brightness": False,
    "realtime_dmx_mode": "MultiRGB",
    "start_universe_setting": 1,
    "dmx_address_start": 1,
    "inactivity_timeout": 1,
}


# adds the {setting: ..., user: ...} thing to the defaults dict
def parse_default_rml_setting(setting):
    key, value = setting
    return (key, {"setting": value, "user_enabled": False})


# creates validators for the different rml preferences
def rml_validator_generator(data_type):
    return vol.Schema(
        {
            vol.Optional("setting"): data_type,
            vol.Optional("user_enabled"): bool,
        }
    )


# creates the vol.optionals using the above two functions
def rml_optional_generator(setting):
    key, default = setting
    return (
        vol.Optional(key, default=default),
        rml_validator_generator(type(default["setting"])),
    )


# generate the default settings with the setting, user enabled dict thing
_default_rml_settings = dict(
    map(parse_default_rml_setting, _default_rml_settings.items())
)

# generate the config schema to validate changes
RML_CONFIG_SCHEMA = vol.Schema(
    dict(map(rml_optional_generator, _default_rml_settings.items()))
)

CORE_CONFIG_SCHEMA = vol.Schema(
    {
        vol.Optional("host", default="0.0.0.0"): str,
        vol.Optional("port", default=8888): int,
        vol.Optional("port_s", default=8443): int,
        vol.Optional("dev_mode", default=False): bool,
        vol.Optional("devices", default=[]): list,
        vol.Optional("virtuals", default=[]): list,
        vol.Optional("audio", default={}): dict,
        vol.Optional("melbanks", default={}): dict,
        vol.Optional("wls_presets", default={}): dict,
        vol.Optional("user_presets", default={}): dict,
        vol.Optional("scenes", default={}): dict,
        vol.Optional("integrations", default=[]): list,
        vol.Optional("visualisation_fps", default=30): vol.All(
            int, vol.Range(1, 60)
        ),
        vol.Optional("visualisation_maxlen", default=50): vol.All(
            int, vol.Range(5, 300)
        ),
        vol.Optional(
            "global_transitions",
            description="Các thay đổi đối với bất kỳ kiểu chuyển tiếp nào của đèn ảo đều áp dụng cho tất cả các đèn ảo khác",
            default=True,
        ): bool,
        vol.Optional("user_colors", default={}): dict,
        vol.Optional("user_gradients", default={}): dict,
        vol.Optional("scan_on_startup", default=False): bool,
        vol.Optional("rml_preferences", default={}): dict,
        vol.Optional(
            "configuration_version", default=CONFIGURATION_VERSION
        ): str,
        vol.Optional("global_brightness", default=1.0): vol.All(
            vol.Coerce(float), vol.Range(0, 1.0)
        ),
    },
    extra=vol.ALLOW_EXTRA,
)


def load_logger():
    global _LOGGER
    _LOGGER = logging.getLogger(__name__)


def get_default_config_directory() -> str:
    """Get the default configuration directory"""

    base_dir = (
        os.getenv("APPDATA") if os.name == "nt" else os.path.expanduser("~")
    )
    return os.path.join(base_dir, CONFIG_DIRECTORY)


def get_config_file(config_dir: str) -> str:
    """Finds a supported configuration file in the provided directory"""

    json_path = os.path.join(config_dir, CONFIG_FILE_NAME)
    if os.path.isfile(json_path) is False:  # Can't find a JSON file
        return None  # No Valid Configs, return None to build another one
    return json_path  # Return the JSON file if we find one.


def get_preset_file(config_dir: str) -> str:
    """Finds a supported preset file in the provided directory"""

    json_path = os.path.join(config_dir, PRESETS_FILE_NAME)
    if os.path.isfile(json_path) is False:  # Can't find a JSON file
        return None  # No Valid Configs, return None to build another one
    return json_path  # Return the JSON file if we find one.


def get_profile_dump_location(config_dir) -> str:
    date_time = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    return os.path.join(config_dir, f"Wls_{date_time}.profile")


def get_log_file_location(config_dir):
    log_file_path = os.path.abspath(os.path.join(config_dir, "Wls.log"))
    return log_file_path


def get_ssl_certs(config_dir) -> tuple:
    """Finds ssl certificate files in config dir"""
    ssl_dir = os.path.join(config_dir, "ssl")

    if not os.path.exists(ssl_dir):
        return None

    key_path = os.path.join(ssl_dir, PRIVATE_KEY_FILE)
    chain_path = os.path.join(ssl_dir, CHAIN_KEY_FILE)

    if os.path.isfile(key_path) and os.path.isfile(key_path):
        return (chain_path, key_path)
    return None


def create_default_config(config_dir: str) -> str:
    """Creates a default configuration in the provided directory"""

    config_path = os.path.join(config_dir, CONFIG_FILE_NAME)
    try:
        with open(config_path, "w", encoding="utf-8") as file:
            json.dump(
                CORE_CONFIG_SCHEMA({}),
                file,
                ensure_ascii=False,
                sort_keys=True,
                indent=4,
            )
        return config_path

    except OSError:
        print(f"Không thể tạo tệp cấu hình mặc định {config_path}.")

        return None


def ensure_config_file(config_dir: str) -> str:
    """Checks if a config file exists, and otherwise creates one"""

    ensure_config_directory(config_dir)
    config_path = get_config_file(config_dir)
    if config_path is None:
        config_path = create_default_config(config_dir)

    return config_path


def check_preset_file(config_dir: str) -> str:

    ensure_config_directory(config_dir)
    presets_path = get_preset_file(config_dir)
    if presets_path is None:
        return None

    return presets_path


def ensure_config_directory(config_dir: str) -> None:
    """Validate that the config directory is valid."""

    # If an explicit path is provided simply check if it exist and failfast
    # if it doesn't. Otherwise, if we have the default directory attempt to
    # create the file
    if not os.path.isdir(config_dir):
        try:
            os.mkdir(config_dir)
        except OSError:
            print(
                ("Lỗi: Không thể tạo thư mục cấu hình {}").format(
                    config_dir
                )
            )
            sys.exit(1)


def load_config(config_dir: str) -> dict:
    """Validates and loads the configuration file in the provided directory"""

    config_file = ensure_config_file(config_dir)
    print(
        f"Đang tải tệp cấu hình: {os.path.join(os.path.abspath(config_dir), CONFIG_FILE_NAME)}"
    )
    try:

        with open(config_file, encoding="utf-8") as file:
            config_json = json.load(file)
            try:
                # If there's no config version in the config, it's pre-1.0.0 and won't work
                # Probably scope to iterate through it and create a virtual for every device, but that's beyond me
                _LOGGER.info(
                    f"Phiên bản cấu hình WiFi Led Studio: {config_json['configuration_version']}"
                )
                assert parse_version(
                    config_json["configuration_version"]
                ) == parse_version(CONFIGURATION_VERSION)
                return CORE_CONFIG_SCHEMA(config_json)
            except (KeyError, AssertionError):
                create_backup(config_dir, config_file, "VERSION")
                _LOGGER.warning(
                    f"Phiên bản cấu hình WiFi Led Studio: {CONFIGURATION_VERSION}, phiên bản cấu hình của bạn: {config_json.get('configuration_version', 'UNDEFINED (old!)')}"
                )
                try:
                    config = migrate_config(config_json)
                    save_config(config, config_dir)
                except Exception as e:
                    _LOGGER.exception(
                        f"Không thể di chuyển cấu hình của bạn sang tiêu chuẩn mới :( Cấu hình cũ của bạn được sao lưu an toàn. Vui lòng cho Rainbow Music Led biết điều gì đã xảy ra: {e}"
                    )
                    config = {}
                return CORE_CONFIG_SCHEMA(config)
    except json.JSONDecodeError:
        create_backup(config_dir, config_file, "DECODE")
        return CORE_CONFIG_SCHEMA({})
    except OSError:
        create_backup(config_dir, config_file, "OSERROR")
        return CORE_CONFIG_SCHEMA({})


def migrate_config(old_config):
    """
    attempts to update an old config to a working state
    """
    _LOGGER.warning("Đang cố chuyển cấu hình cũ sang phiên bản mới ...")

    # most invalid keys were from invalid frequency ranges.
    # this replacement dict should fix that
    replacement_frequency_ranges = {
        "Siêu trầm (1-20Hz)": "Nhịp",
        "Trầm phụ (20-60Hz)": "Thấp (nhịp+trầm)",
        "Trầm (60-250Hz)": "Thấp (nhịp+trầm)",
        "Trung thấp (250-500Hz)": "Thấp (nhịp+trầm)",
        "Trung (500Hz-2kHz)": "Trung",
        "Trung trên (2Khz-4kHz)": "Trung",
        "Trung cao (4kHz-6kHz)": "Cao",
        "Tần số cao (6kHz-24kHz)": "Cao",
    }

    class DummyWls:
        def dev_enabled(_):
            return False

    import copy

    import voluptuous as vol

    from wls.effects import Effects

    effects = Effects(DummyWls()).classes()

    # initialise some things that will help us match up old effect info to new effect info
    def get_matching_effect_id(dirty_effect_id):
        def clean_effect_id(effect_id):
            return effect_id.lower().replace("(reactive)", "").replace("_", "")

        candidate_effect_id = clean_effect_id(dirty_effect_id)
        for effect_id in effects:
            if clean_effect_id(effect_id) == candidate_effect_id:
                return effect_id
        else:
            return None

    def sanitise_effect_config(effect_type, old_config):
        # checks each config key against the current schema, discarding any values that dont match
        schema = effects[effect_type].schema().schema
        new_config = {}
        for old_key in old_config:
            new_key = old_key.replace("colour", "color")
            if new_key in schema:
                try:
                    if (
                        old_key == "frequency_range"
                        and old_config.get(old_key)
                        not in replacement_frequency_ranges.values()
                    ):
                        old_config[old_key] = replacement_frequency_ranges[
                            old_config.get(old_key)
                        ]
                    schema[new_key](old_config[old_key])
                    new_config[new_key] = old_config[old_key]
                except (vol.MultipleInvalid, vol.InInvalid, Exception):
                    _LOGGER.warning(
                        f"Cài trước cho {effect_type} với cấu hình {old_key} : {old_config[old_key]} không có hiệu lực. Loại bỏ."
                    )
                    continue
            else:
                _LOGGER.warning(
                    f"Cài trước cho {effect_type} không thể khớp với cấu hình {old_key}. Loại bỏ khỏi cài trước."
                )
                continue
        return new_config

    new_config = copy.deepcopy(old_config)

    # if not using new config "audio_device", delete audio config
    if not old_config.get("audio", {}).get("audio_device", None):
        new_config.pop("audio", None)

    # remove old transition things
    new_config.pop("crossfade", None)
    new_config.pop("fade", None)

    # update devices
    new_config["devices"] = []
    for device in old_config.get("devices", ()):
        if device["type"].lower() == "fxmatrix":
            _LOGGER.warning(
                "Thiết bị FXMatrix không còn được hỗ trợ. Thêm nó dưới dạng UDP hoặc RML thuần túy."
            )
            continue
        device.pop("effect", None)
        new_config["devices"].append(device)

    # if displays/virtuals are present, remove their effects and rename to virtuals
    # else if no virtuals saved, create virtuals for all the devices
    virtuals = new_config.pop("displays", None) or new_config.pop(
        "virtuals", None
    )
    if virtuals:
        for virtual in virtuals:
            effect = virtual.get("effect", None)
            if effect:
                effect_id, effect_config = (
                    effect.get("type", None),
                    effect.get("config", None),
                )
                if effect_id:
                    new_effect_id = get_matching_effect_id(effect_id)
                    if not new_effect_id:
                        _LOGGER.warning(
                            f"Không thể khớp hiệu ứng {effect_id} với bất kỳ hiệu ứng hiện tại nào. Bỏ hiệu ứng này khỏi đèn ảo {virtual['id']}."
                        )
                        continue
                    new_effect_config = sanitise_effect_config(
                        new_effect_id, effect_config
                    )
                virtual["effect"] = {
                    "config": new_effect_config,
                    "type": new_effect_id,
                }
        new_config["virtuals"] = virtuals
    else:  # time to make some virtuals
        from wls.utils import generate_id

        new_config["virtuals"] = []
        for device in new_config["devices"]:
            # Generate virtual configuration for the device
            name = device["config"]["name"]
            _LOGGER.info(f"Tạo ảo cho thiết bị {name}")

            virtual_config = {
                "name": name,
                # "icon_name": device_config["icon_name"],
            }
            segments = [
                [device["id"], 0, device["config"]["pixel_count"] - 1, False]
            ]

            new_config["virtuals"].append(
                {
                    "id": generate_id(name),
                    "is_device": device["id"],
                    "config": virtual_config,
                    "segments": segments,
                }
            )

    # clean up user presets. effect names have changed, we'll try to clean them up here
    user_presets = new_config.pop("custom_presets", ()) or new_config.pop(
        "user_presets", ()
    )
    new_config["user_presets"] = {}
    for effect_id in user_presets:
        new_effect_id = get_matching_effect_id(effect_id)
        if not new_effect_id:
            _LOGGER.warning(
                f"Không thể khớp hiệu ứng {effect_id} với bất kỳ hiệu ứng hiện tại nào. Loại bỏ các cài trước cho hiệu ứng này."
            )
            continue
        new_config["user_presets"][new_effect_id] = {}
        for preset_id in user_presets[effect_id]:
            new_config["user_presets"][new_effect_id][preset_id] = {
                "name": user_presets[effect_id][preset_id]["name"],
                "config": sanitise_effect_config(
                    new_effect_id, user_presets[effect_id][preset_id]["config"]
                ),
            }

    # clean up scenes. if you are reading this, sorry for the confusing variable naming. i've tried my best :D
    scenes = new_config.pop("scenes", ())
    new_config["scenes"] = {}
    if scenes:
        scenes_mode = next(
            mode
            for mode in scenes[next(iter(scenes))]
            if mode in ("devices", "displays", "virtuals")
        )
    for scene_id in scenes:
        virtuals_ish = scenes[scene_id].pop(scenes_mode, ())
        new_virtuals = {}
        for virtual_ish in virtuals_ish:
            # if scenes are populated by devices, then we should by now have virtuals made for each device.
            # we need to find the corresponding virtual for the device
            if scenes_mode == "devices":
                corresponding_virtual = next(
                    (
                        real_virtual["id"]
                        for real_virtual in new_config["virtuals"]
                        if real_virtual.get("is_device", None) == virtual_ish
                    ),
                    None,
                )
                if not corresponding_virtual:
                    _LOGGER.warning(
                        f"Không thể khớp đèn {device} với bất kỳ đèn ảo nào. Loại bỏ đèn này khỏi cảnh {scene_id}."
                    )
                    continue
                actual_virtual = corresponding_virtual
            else:
                # if it's displays or virtuals, these should already exist in the user's config
                actual_virtual = virtual_ish
            # with the virtuals_ish now sanitised to an actual virtual, we need to clean up the effect type and config
            effect_id, effect_config = (
                virtuals_ish[virtual_ish].get("type", None),
                virtuals_ish[virtual_ish].get("config", None),
            )
            if effect_id and effect_config:
                new_effect_id = get_matching_effect_id(effect_id)
                if not new_effect_id:
                    _LOGGER.warning(
                        f"Không thể khớp hiệu ứng {effect_id} với bất kỳ hiệu ứng hiện tại nào. Loại bỏ hiệU ứng này khỏi cảnh {scene_id}."
                    )
                    continue
                new_effect_config = sanitise_effect_config(
                    new_effect_id, effect_config
                )
                new_virtuals[actual_virtual] = {
                    "config": new_effect_config,
                    "type": new_effect_id,
                }
            else:
                new_virtuals[actual_virtual] = {}

        new_config["scenes"][scene_id] = {
            "virtuals": new_virtuals,
            "name": scenes[scene_id]["name"],
        }

    _LOGGER.warning("Đã hoàn tất quá trình di chuyển cấu hình.")
    return new_config


def create_backup(config_dir, config_file, errortype):
    """This function creates a backup of the current configuration file - it uses the format dd-mm-yyyy_hh-mm-ss for the backup file.

    Args:
        config_dir (path): The path to the current configuration directory
        config_file (path): The path to the current configuration file
        errortype (string): The type of error we encounter to allow for better logging
    """

    date = datetime.datetime.now().strftime("%d-%m-%y_%H-%M-%S")
    backup_location = os.path.join(config_dir, f"cauhinh_duphong_{date}.json")
    try:
        os.rename(config_file, backup_location)
    except OSError:
        shutil.copy2(config_file, backup_location)

    if errortype == "DECODE":
        _LOGGER.warning(
            "Lỗi khi tải cấu hình. Đã tạo bản sao lưu, cấu hình trống được sử dụng."
        )

    if errortype == "VERSION":
        _LOGGER.warning("Đã phát hiện cấu hình không tương thích. Đã tạo bản sao lưu.")

    if errortype == "OSERROR":
        _LOGGER.warning(
            "Không thể mở cấu hình. Sao lưu Đã tạo, cấu hình trống được sử dụng."
        )

    _LOGGER.warning(f"Sao lưu đặt tại: {backup_location}")


def save_config(config: dict, config_dir: str) -> None:
    """Saves the configuration to the provided directory"""

    config_file = ensure_config_file(config_dir)
    _LOGGER.info(("Đang lưu tệp cấu hình vào {}").format(config_dir))
    config["configuration_version"] = CONFIGURATION_VERSION
    config_view = dict(config)
    unneeded_keys = ["wls_presets"]
    for key in [key for key in config_view if key in unneeded_keys]:
        del config_view[key]

    with open(config_file, "w", encoding="utf-8") as file:
        json.dump(
            config_view, file, ensure_ascii=False, sort_keys=True, indent=4
        )


def save_presets(config: dict, config_dir: str) -> None:
    """Saves the configuration to the provided directory"""

    presets_file = check_preset_file(config_dir)
    _LOGGER.info(("Đang lưu các cài trước của người dùng vào {}").format(config_dir))

    config_view = dict(config)
    for key in [key for key in config_view if key != "user_presets"]:
        del config_view[key]

    with open(presets_file, "w", encoding="utf-8") as file:
        json.dump(
            config_view, file, ensure_ascii=False, sort_keys=True, indent=4
        )
