import logging
import socket

import numpy as np
import voluptuous as vol

from wls.devices import NetworkedDevice, packets
from wls.events import DevicesUpdatedEvent
from wls.devices.__init__ import(
    AVAILABLE_FPS,
    fps_validator,
)

_LOGGER = logging.getLogger(__name__)


class OpenRGB(NetworkedDevice):
    """OpenRGB protocol device support"""

    @staticmethod
    @property
    def CONFIG_SCHEMA():
        return vol.Schema(
            {
                vol.Required(
                "name", description="Tên dễ nhớ cho đèn"
                ): str,
                vol.Required(
                    "name", description="Tên đèn"
                ): str,
                vol.Required(
                    "openrgb_id",
                    description="ID của thiết bị OpenRGB (ở trong OpenRGB).",
                    default=0,
                ): vol.All(int, vol.Range(min=0)),
                vol.Required(
                    "pixel_count",
                    description="Số lượng LED",
                    default=1,
                ): vol.All(int, vol.Range(min=1)),
                vol.Required(
                    "port",
                    description="Cổng cho thiết bị UDP",
                    default=6742,
                ): vol.All(int, vol.Range(min=1, max=65535)),
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
        self._wls = wls
        self.ip_address = self._config["ip_address"]
        self.port = self._config["port"]
        self.openrgb_device_id = self._config["openrgb_id"]
        self._online = True

    def activate(self):
        try:
            from openrgb import OpenRGBClient

            try:
                self.openrgb_device = OpenRGBClient(
                    self.ip_address, self.port, "Wls", 3  # protocol_version
                )
                self.openrgb_device = self.openrgb_device.devices[
                    self.openrgb_device_id
                ]
                self._online = True
            except (ConnectionRefusedError, TimeoutError):
                _LOGGER.warning(
                    f"{self.openrgb_device_id} không liên lạc được. Máy chủ api có đang chạy không?"
                )
                self._online = False
                return
            # check for eedevice

            device_supports_direct = False
            for mode in self.openrgb_device.modes:
                if mode.name.lower() == "direct":
                    device_supports_direct = True
            if not device_supports_direct:
                raise ValueError()
        except ImportError:
            _LOGGER.critical("Không thể tải thư viện openrgb")
            self.deactivate()
        except IndexError:
            _LOGGER.critical(
                f"Không thể tìm thấy thiết bị openRGB có ID: {self.openrgb_device_id}"
            )
            self._online = False
            self.deactivate()
        except ValueError:
            _LOGGER.critical(
                f"{self.openrgb_device_id} không hỗ trợ chế độ trực tiếp và không phù hợp với các hiệu ứng phát trực tiếp từ Wls"
            )
            self.deactivate()
        else:
            self._online = True
            super().activate()

    def deactivate(self):
        super().deactivate()

    def flush(self, data):
        """Flush LED data to the strip"""
        try:
            OpenRGB.send_out(
                self.openrgb_device.comms.sock,
                data,
                self.openrgb_device.id,
            )
        except AttributeError:
            self.activate()
        except ConnectionAbortedError:
            _LOGGER.warning(f"Thiết bị ngắt kết nối: {self.openrgb_device_id}")
            self._wls.events.fire_event(DevicesUpdatedEvent(self.id))
            self._online = False
            self.deactivate()

    @staticmethod
    def send_out(sock: socket.socket, data: np.ndarray, device_id: int):
        packet = packets.build_openrgb_packet(data, device_id)
        sock.send(packet)
