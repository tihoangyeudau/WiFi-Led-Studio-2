import logging
import tkinter as tk
from tkinter import messagebox
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

class AmbilightUSBDevice(SerialDevice):
    """Ambilight USB device support"""

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
                vol.Required(
                    "baudrate", description="tốc độ truyền", default=115200
                ): int,
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
        except serial.SerialException as e:
            _LOGGER.error("SerialException occurred: %s", str(e))
            # Create a simple popup dialog with OK and Reconnect buttons using tkinter
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            messagebox.showinfo("SerialException", "Tín hiệu USB bị ngắt kết nối. Bạn hãy kiểm tra và cắm lại dây USB nhé?")
            root.destroy()  # Destroy the root window
            self.reconnect()
