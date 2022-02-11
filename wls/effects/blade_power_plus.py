import logging
from collections import namedtuple

import numpy as np
import voluptuous as vol

from wls.color import validate_color
from wls.effects.audio import AudioReactiveEffect
from wls.effects.hsv_effect import HSVEffect

RGB = namedtuple("RGB", "red, green, blue")
hsv = namedtuple("hsv", "hue, saturation, value")

_LOGGER = logging.getLogger(__name__)


class BladePowerPlus(AudioReactiveEffect, HSVEffect):

    NAME = "RML pro"
    CATEGORY = "Cổ điển"

    _power_funcs = {
        "Nhịp": "beat_power",
        "Trầm": "bass_power",
        "Thấp (nhịp+trầm)": "lows_power",
        "Trung": "mids_power",
        "Cao": "high_power",
    }

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "mirror",
                description="Phản chiếu",
                default=True,
            ): bool,
            vol.Optional(
                "blur",
                description="Làm mờ",
                default=2,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=10)),
            vol.Optional(
                "decay",
                description="Tỷ lệ phân rã màu sắc",
                default=0.7,
            ): vol.All(vol.Coerce(float), vol.Range(0, 1)),
            vol.Optional(
                "multiplier",
                description="Làm cho thanh phản ứng lớn hơn/nhỏ hơn",
                default=0.7,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            vol.Optional(
                "background_color",
                description="Màu nền",
                default="#000000",
            ): validate_color,
            vol.Optional(
                "frequency_range",
                description="Dải tần số để phát hiện nhịp",
                default="Trung",
            ): vol.In(list(_power_funcs.keys())),
            vol.Optional(
                "invert_roll",
                description="Đảo ngược hướng của cuộn gradient",
                default=False,
            ): bool,
        }
    )

    def on_activate(self, pixel_count):
        self.bar = 0
        self.hsv_array[:, 0] = np.linspace(0, 1, self.pixel_count)
        self.hsv_array[:, 1] = 1

    def config_updated(self, config):
        self.power_func = self._power_funcs[self._config["frequency_range"]]

    def audio_data_updated(self, data):
        # Get filtered bar power
        self.bar = (
            getattr(data, self.power_func)() * self._config["multiplier"] * 2
        )

    def render_hsv(self):
        # Must be zeroed every cycle to clear the previous frame
        bar_idx = int(self.bar * self.pixel_count)
        self.hsv_array[:, 2] *= self._config["decay"] / 2 + 0.45
        self.hsv_array[:bar_idx, 2] = self._config["brightness"]
