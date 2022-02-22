import logging

import voluptuous as vol
from pkg_resources import parse_version

from wls.devices import NetworkedDevice
from wls.devices.ddp import DDPDevice
from wls.devices.e131 import E131Device
from wls.devices.udp import UDPRealtimeDevice
from wls.utils import RML, RML2

_LOGGER = logging.getLogger(__name__)


class RMLDevice(NetworkedDevice):
    """
    Dedicated RML device support
    This class fetches its config (px count, etc) from the RML device
    at launch, and lets the user choose a sync mode to use.
    """

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "sync_mode",
                description="Giao thức truyền trực tuyến tới thiết bị RML. Khuyến nghị: UDP <480 LED, DDP> 480 LED",
                default="UDP",
            ): vol.In(["UDP", "DDP", "E131"]),
            vol.Optional(
                "timeout",
                description="Thời gian giữa hiệu ứng WiFi Led Studio tắt và hiệu ứng đèn Rainbow Music Led kích hoạt",
                default=1,
            ): vol.All(int, vol.Range(0, 255)),
        }
    )

    SYNC_MODES = {
        "UDP": UDPRealtimeDevice,
        "DDP": DDPDevice,
        "E131": E131Device,
    }

    DEVICE_CONFIGS = {
        "UDP": {
            "name": None,
            "ip_address": None,
            "pixel_count": None,
            "port": 7778,
            "udp_packet_type": "DNRGB",
            "timeout": 1,
            "minimise_traffic": True,
        },
        "DDP": {
            "name": None,
            "ip_address": None,
            "pixel_count": None,
        },
        "E131": {
            "name": None,
            "ip_address": None,
            "pixel_count": None,
            "universe": 1,
            "universe_size": 510,
            "channel_offset": 0,
            "packet_priority": 100,
        },
    }

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self.subdevice = None

    def config_updated(self, config):
        if not isinstance(
            self.subdevice, self.SYNC_MODES[self._config["sync_mode"]]
        ):
            self.setup_subdevice()

    def setup_subdevice(self):
        if self.subdevice is not None:
            self.subdevice.deactivate()

        device = self.SYNC_MODES[self._config["sync_mode"]]
        config = self.DEVICE_CONFIGS[self._config["sync_mode"]]
        config["name"] = self._config["name"]
        config["ip_address"] = self._config["ip_address"]
        config["pixel_count"] = self._config["pixel_count"]
        config["refresh_rate"] = self._config["refresh_rate"]

        self.subdevice = device(self._wls, config)
        self.subdevice._destination = self._destination

    def activate(self):
        self.RMLReceiver = False
        self.device_ip = RML2.resolve_destination(self._config["ip_address"])
        if not self.device_ip:
            _LOGGER.warning(
                f"Không thể giải quyết điểm đến {self._config['ip_address']}, Huỷ kích hoạt đèn {self.name}. Hãy đảm bảo IP/hostname chính xác và đèn đang được kết nối."
            )
            return
            # If the device is a RML device, turn it on
        if RML2.rml_identifier(self.device_ip, self.name):
            self.RMLReceiver = True
            self.rml_state = RML2.rml_power_state(self.device_ip, self.name)
            if self.rml_state is False:
                RML2.turn_rml_on(self.device_ip, self.name)
        if self.subdevice is None:
            self.setup_subdevice()
        self.subdevice.activate()
        super().activate()

    def deactivate(self):
        if self.subdevice is not None:
            self.subdevice.deactivate()
        super().deactivate()
        if self.RMLReceiver is True and self.rml_state is True:
            RML2.turn_rml_off(self.device_ip, self.name)

    def flush(self, data):
        self.subdevice.flush(data)

    async def async_initialize(self):
        await super().async_initialize()
        # if not self._destination:
        #     self.setup_subdevice()
        #     return
        self.rml = RML(self._destination)
        rml_config = await self.rml.get_config()

        led_info = rml_config["leds"]
        rml_name = rml_config["name"]
        rml_count = led_info["count"]
        rml_rgbmode = led_info["rgbw"]
        rml_version = rml_config["ver"]

        rml_config = {
            "name": rml_name,
            "pixel_count": rml_count,
            "rgbw_led": rml_rgbmode,
        }

        self._config.update(rml_config)
        self.setup_subdevice()

        # Currently *assuming* that this PR gets released in 0.13
        # https://github.com/Aircoookie/RML/pull/1944
        if parse_version(rml_version) >= parse_version("0.13.0"):
            _LOGGER.info(
                f"Phiên bản Rainbow Music Led hỗ trợ cài đặt API đồng bộ hóa: {rml_version}"
            )
            rml_sync_settings = await self.rml.get_sync_settings()
        # self.rml.enable_realtime_gamma()
        # self.rml.set_inactivity_timeout(self._config["timeout"])
        # self.rml.first_universe()
        # self.rml.first_dmx_address()
        # self.rml.multirgb_dmx_mode()

        # await self.rml.flush_sync_settings()
