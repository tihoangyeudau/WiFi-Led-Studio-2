import logging
import socket
import struct

import voluptuous as vol

from wls.devices import NetworkedDevice

_LOGGER = logging.getLogger(__name__)


class OpenPixelControl(NetworkedDevice):
    """OpenPixelControl device support"""

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "pixel_count",
                description="Số lượng LED",
                default=1,
            ): vol.All(int, vol.Range(min=1)),
            vol.Required(
                "channel",
                description="Kênh gửi dữ liệu pixel",
                default=0,
            ): vol.All(int, vol.Range(min=0, max=255)),
        }
    )

    def activate(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _LOGGER.info(
            f"Open Pixel Control cho {self.config['name']} đã bắt đầu."
        )
        super().activate()

    def deactivate(self):
        super().deactivate()
        _LOGGER.info(
            f"Open Pixel Control cho {self.config['name']} đã dừng."
        )
        self._sock = None

    def flush(self, data):
        try:
            OpenPixelControl.send_out(
                self,
                self._sock,
                self.destination,
                7890,
                data,
            )
        except AttributeError:
            self.activate()

    @staticmethod
    def send_out(
        self,
        sock,
        dest,
        port,
        data,
    ):
        header = struct.pack(
            ">BBH", self.config["channel"], 0, self.config["pixel_count"] * 3
        )
        pieces = [
            struct.pack(
                "BBB",
                min(255, max(0, int(r))),
                min(255, max(0, int(g))),
                min(255, max(0, int(b))),
            )
            for r, g, b in data
        ]
        message = header + b"".join(pieces)
        sock.sendto(
            bytes(message),
            (dest, port),
        )
