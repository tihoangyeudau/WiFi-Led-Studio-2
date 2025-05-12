import logging

import voluptuous as vol

from wls.devices import NetworkedDevice
from wls.devices.ddp import DDPDevice
from wls.devices.udp import UDPRealtimeDevice
from wls.utils import RML

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
                description="Giao thức truyền trực tuyến tới thiết bị RML. Khuyến nghị: DDP cho v0.13 trở lên. Sử dụng UDP cho các phiên bản cũ hơn.",
                default="auto",
            ): vol.In(["auto", "DDP", "UDP"]),
            vol.Optional(
                "timeout",
                description="Thời gian giữa hiệu ứng WiFi Led Studio tắt và hiệu ứng đèn Rainbow Music Led kích hoạt",
                default=1,
            ): vol.All(int, vol.Range(0, 255)),
        }
    )

    SYNC_MODES = {
        "DDP": DDPDevice,
        "UDP": UDPRealtimeDevice,
    }

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self.subdevice = None

        self.device_configs = {
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
            }
        }

    def config_updated(self, config):
        if not isinstance(
            self.subdevice, self.SYNC_MODES[self._config["sync_mode"]]
        ):
            self.setup_subdevice()

    def setup_subdevice(self):
        if self.subdevice is not None:
            self.subdevice.deactivate()

        device = self.SYNC_MODES[self._config["sync_mode"]]
        config = self.device_configs[self._config["sync_mode"]]
        config["name"] = self._config["name"]
        config["ip_address"] = self._config["ip_address"]
        config["pixel_count"] = self._config["pixel_count"]
        config["refresh_rate"] = self._config["refresh_rate"]

        self.subdevice = device(self._wls, config)
        self.subdevice._destination = self._destination

    def activate(self):
        """Activate the device and its subdevice"""
        # Kiểm tra xem thiết bị có được hỗ trợ không
        if hasattr(self, '_not_supported') and self._not_supported:
            return  # Dừng việc kích hoạt tại đây

        try:
            import asyncio
            if hasattr(self, 'rml'):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.rml.set_power_state(True))
                else:
                    loop.run_until_complete(self.rml.set_power_state(True))
        except Exception as e:
            _LOGGER.error(f"Error activating RML device: {e}")

        if self.subdevice is None:
            self.setup_subdevice()
        self.subdevice.activate()
        super().activate()

    def deactivate(self):
        """Deactivate the device and its subdevice"""
        try:
            import asyncio
            if hasattr(self, 'rml'):
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.rml.set_power_state(False))
                else:
                    loop.run_until_complete(self.rml.set_power_state(False))
        except Exception as e:
            _LOGGER.error(f"Error deactivating RML device: {e}")

        if self.subdevice is not None:
            self.subdevice.deactivate()

        super().deactivate()

    async def resolve_address(self, success_callback=None):
        await super().resolve_address(success_callback)
        if self.subdevice is not None:
            self.subdevice._destination = self._destination

    def flush(self, data):
        self.subdevice.flush(data)

    async def async_initialize(self):
        await super().async_initialize()

        # Nếu không có _destination, không thể tiếp tục
        if not self._destination:
            return

        try:
            self.rml = RML(self._destination)
            rml_config = await self.rml.get_config()

            # Kiểm tra kết quả từ get_config()
            if rml_config is None:
                # Đánh dấu thiết bị không trực tuyến để ngăn nó được kích hoạt
                self._online = False
                # Xóa _destination để ngăn mọi hoạt động mạng trong tương lai
                self._destination = None
                # Gán một cờ để đánh dấu rằng thiết bị không được hỗ trợ
                self._not_supported = True
                return

            led_info = rml_config["leds"]
            rml_name = rml_config["name"]
            rml_count = led_info["count"]
            rml_rgbmode = led_info["rgbw"]
            rml_udpport = rml_config.get("udpport", None)

            rml_config = {
                "name": rml_name,
                "pixel_count": rml_count,
                "rgbw_led": rml_rgbmode,
            }

            # Thiết lập sync_mode dựa trên giá trị của rml_udpport
            if rml_udpport is None or not rml_udpport:
                self._config["sync_mode"] = "DDP"
            else:
                self._config["sync_mode"] = "UDP"

            self._config.update(rml_config)
            self._not_supported = False  # Đánh dấu thiết bị được hỗ trợ
            self.setup_subdevice()
        except Exception as e:
            _LOGGER.error(f"Đèn có IP {self._destination}: Lỗi trong khi khởi tạo: {str(e)}")
            self._online = False
            self._destination = None