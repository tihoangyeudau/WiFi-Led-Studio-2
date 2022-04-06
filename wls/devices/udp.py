import logging
import time

import numpy as np
import voluptuous as vol

from wls.devices import UDPDevice, packets
from wls.devices.__init__ import(
    fps_validator,
)

_LOGGER = logging.getLogger(__name__)

SUPPORTED_PACKETS = ["DRGB", "WARLS", "DRGBW", "DNRGB", "adaptive_smallest"]


class UDPRealtimeDevice(UDPDevice):
    """Generic UDP Realtime device support"""

    CONFIG_SCHEMA = vol.Schema(
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
                "udp_packet_type",
                description="Mã hóa gói RGB",
                default="DRGB",
            ): vol.In(list(SUPPORTED_PACKETS)),
            vol.Optional(
                "timeout",
                description="Vài giây để đợi sau khi gói nhận được cuối cùng để nhường quyền kiểm soát đèn",
                default=1,
            ): vol.All(int, vol.Range(min=1, max=255)),
            vol.Optional(
                "minimise_traffic",
                description="Sẽ không gửi cập nhật nếu không có gì thay đổi trên đèn LED",
                default=True,
            ): bool,
            vol.Optional(
                "refresh_rate",
                description="Target rate that pixels are sent to the device",
                default=32,
            ): fps_validator,
        }
    )

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self._device_type = "UDP Realtime"
        self.last_frame = np.full((config["pixel_count"], 3), -1)
        self.last_frame_sent_time = 0

    def flush(self, data):
        try:
            self.choose_and_send_packet(
                data,
                self._config["timeout"],
            )
            self.last_frame = np.copy(data)
        except AttributeError:
            self.activate()

    def choose_and_send_packet(
        self,
        data,
        timeout,
    ):
        frame_size = len(data)

        frame_is_equal_to_last = self._config[
            "minimise_traffic"
        ] and np.array_equal(data, self.last_frame)

        if self._config["udp_packet_type"] == "DRGB" and frame_size <= 490:
            udpData = packets.build_drgb_packet(data, timeout)
            self.transmit_packet(udpData, frame_is_equal_to_last)

        elif self._config["udp_packet_type"] == "WARLS" and frame_size <= 255:
            udpData = packets.build_warls_packet(
                data, timeout, self.last_frame
            )
            self.transmit_packet(udpData, frame_is_equal_to_last)

        elif self._config["udp_packet_type"] == "DRGBW" and frame_size <= 367:
            udpData = packets.build_drgbw_packet(data, timeout)
            self.transmit_packet(udpData, frame_is_equal_to_last)

        elif self._config["udp_packet_type"] == "DNRGB":
            number_of_packets = int(np.ceil(frame_size / 489))
            for i in range(number_of_packets):
                start_index = i * 489
                end_index = start_index + 489
                udpData = packets.build_dnrgb_packet(
                    data[start_index:end_index], timeout, start_index
                )
                self.transmit_packet(udpData, frame_is_equal_to_last)

        elif (
            self._config["udp_packet_type"] == "adaptive_smallest"
            and frame_size <= 255
        ):
            # compare potential size of WARLS packet to DRGB packet
            if (
                np.count_nonzero(np.any(data != self.last_frame, axis=1)) * 4
                < len(data) * 3
            ):
                udpData = packets.build_warls_packet(
                    data, timeout, self.last_frame
                )
                self.transmit_packet(udpData, frame_is_equal_to_last)
            else:
                udpData = packets.build_drgb_packet(data, timeout)
                self.transmit_packet(udpData, frame_is_equal_to_last)

        else:  # fallback
            _LOGGER.warning(
                f"Gói UDP được định cấu hình không chính xác (vui lòng chọn gói hỗ trợ {self._config['pixel_count']} LED): https://facebook.com/rainbowmusicled \n Quay lại gói udp được hỗ trợ."
            )
            if frame_size <= 490:  # DRGB
                udpData = packets.build_drgb_packet(data, timeout)
                self.transmit_packet(udpData, frame_is_equal_to_last)
            else:  # DNRGB
                number_of_packets = int(np.ceil(frame_size / 489))
                for i in range(number_of_packets):
                    start_index = i * 489
                    end_index = start_index + 489
                    udpData = packets.build_dnrgb_packet(
                        data[start_index:end_index], timeout, start_index
                    )
                    self.transmit_packet(udpData, frame_is_equal_to_last)

    def transmit_packet(self, packet, frame_is_equal_to_last: bool):
        timestamp = time.time()
        if frame_is_equal_to_last:
            half_of_timeout = (
                ((self._config["timeout"] * self._config["refresh_rate"]) - 1)
                // 2
            ) / self._config["refresh_rate"]
            if timestamp > self.last_frame_sent_time + half_of_timeout:
                if self._destination is not None:
                    self._sock.sendto(
                        bytes(packet), (self.destination, 7778)
                    )
                    self.last_frame_sent_time = timestamp
        else:
            if self._destination is not None:
                self._sock.sendto(
                    bytes(packet), (self.destination, 7778)
                )
                self.last_frame_sent_time = timestamp
