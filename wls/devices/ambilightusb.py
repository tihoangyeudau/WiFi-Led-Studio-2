import logging

import serial
import voluptuous as vol

from wls.devices import SerialDevice, packets
from wls.devices.__init__ import(
    AVAILABLE_FPS,
    fps_validator,
)

_LOGGER = logging.getLogger(__name__)

COLOR_ORDERS = [
    "RGB",
    "RBG",
    "GRB",
    "BRG",
    "GBR",
    "BGR",
]


class AmbilightUSBDevice(SerialDevice):
    """AmbilightUSB device support"""

    @staticmethod
    @property
    def CONFIG_SCHEMA():
        return vol.Schema(
            {
                vol.Required(
                "name", description="Tên dễ nhớ cho đèn"
                ): str,
                vol.Required(
                    "pixel_count",
                    description="Số lượng LED",
                    default=1,
                ): vol.All(int, vol.Range(min=1)),
                vol.Required(
                    "color_order", description="Thứ tự mầu", default="RGB"
                ): vol.In(list(COLOR_ORDERS)),
                vol.Optional(
                    "refresh_rate",
                    description="Target rate that pixels are sent to the device",
                    default=next(
                        (f for f in AVAILABLE_FPS if f >= 60),
                        list(AVAILABLE_FPS)[-1],
                    ),
                ): fps_validator,
            }
        )

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self._device_type = "AmbilightUSB"
        self.color_order = self._config["color_order"]

    def flush(self, data):
        try:
            self.serial.write(
                packets.build_ambilightusb_packet(data, self.color_order)
            )

        except serial.SerialException:
            _LOGGER.critical(
                "Kết nối nối tiếp bị gián đoạn. Vui lòng kiểm tra kết nối và đảm bảo thiết bị của bạn hoạt động bình thường."
            )
