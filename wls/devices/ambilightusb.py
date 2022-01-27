import logging

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
    """AmbilightUSB device support"""

    @staticmethod
    @property
    def CONFIG_SCHEMA():
        return vol.Schema(
            {
                vol.Required(
                    "pixel_count",
                    description="Number of individual pixels",
                    default=1,
                ): vol.All(int, vol.Range(min=1)),
                vol.Required(
                    "color_order", description="Color order", default="RGB"
                ): vol.In(list(COLOR_ORDERS)),
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
                "Serial Connection Interrupted. Please check connections and ensure your device is functioning correctly."
            )
            self.deactivate()
