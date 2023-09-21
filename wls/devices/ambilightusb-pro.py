import serial
import voluptuous as vol
from wls.devices import SerialDevice, packets

COLOR_ORDERS = [
    "RGB",
    "RBG",
    "GRB",
    "BRG",
    "GBR",
    "BGR",
]

class AmbilightUSBProDevice(SerialDevice):
    """Ambilight USB Pro device support"""

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
        self._device_type = "AmbilightUSB-Pro"
        self.color_order = self._config["color_order"]

    def flush(self, data):
        if self.serial is None:
            print("Không thể gửi dữ liệu: self.serial chưa được khởi tạo")
            self.reconnect()
            self.flush(data)
            return

        try:
            if self.baudrate == 1000000:
                self.serial.write(
                    packets.build_ambilightusbpro_packet(data, self.color_order)
                )
            else:
                self.serial.write(
                    packets.build_ambilightusb_packet(data, self.color_order)
                )
        except serial.SerialException:
            self.reconnect()


