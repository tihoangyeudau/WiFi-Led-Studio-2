import logging
import time
import serial
import voluptuous as vol
from wls.devices import SerialDevice, packets

_LOGGER = logging.getLogger(__name__)

COLOR_ORDERS = [
    "RGB",
    "RBG",
    "GRB",
    "BRG",
    "GBR",
    "BGR",
]

class SkydimondUSBDevice(SerialDevice):
    """Skydimond USB device support"""

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
            }
        )

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self._device_type = "Skydimond USB"
        self.color_order = self._config["color_order"]

    def flush(self, data):
        if self.serial is None or not self.serial.isOpen():
            _LOGGER.error("Không thể gửi dữ liệu: Kiểm tra lại kết nối USB")
            time.sleep(2)
            return

        try:
            if self.version == 115200:
                self.serial.write(
                    packets.build_skydimondusb_rainbowmusicled_dot_com_0981373223_packet(data, self.color_order)
                )
            else:
                self.serial.write(
                    packets.build_skydimondusbpro_rainbowmusicled_dot_com_0981373223_packet(data, self.color_order)
                )
        except serial.SerialException as e:
            _LOGGER.error(f"Không thể gửi dữ liệu: {str(e)}")
            time.sleep(2)
            self.reconnect()