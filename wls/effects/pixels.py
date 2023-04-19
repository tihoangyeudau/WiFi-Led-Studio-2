import logging
import timeit

import numpy as np
import voluptuous as vol

from wls.color import parse_color, validate_color
from wls.effects.temporal import TemporalEffect

_LOGGER = logging.getLogger(__name__)

# Metro intent is to flash a pattern on led strips so end users can look for
# sync between separate light strips due to protocol, wifi conditions or other
# Best configured as a copy virtual across mutliple devices, however uses a
# common derived time base and step count so that seperate devices / virtuals
# with common configurations will be in sync


class PixelsEffect(TemporalEffect):
    NAME = "Điểm ảnh"
    CATEGORY = "Chuẩn đoán"
    HIDDEN_KEYS = ["speed", "background_brightness", "blur", "mirror"]

    start_time = timeit.default_timer()

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "speed",
                default=20.0,
                description="Đã khóa tại 20 fps",
            ): vol.All(vol.Coerce(float), vol.Range(min=20, max=20)),
            vol.Optional(
                "step_period",
                description="Thời gian giữa mỗi bước pixel để sáng lên ",
                default=1.0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=5.0)),
            vol.Optional(
                "background_color",
                description="Màu nền",
                default="#000000",
            ): validate_color,
            vol.Optional(
                "pixel_color",
                description="Màu điểm ảnh sáng lên",
                default="#FFFFFF",
            ): validate_color,
            vol.Optional(
                "build_up",
                description="Điểm ảnh đơn hoặc cụm điểm ảnh",
                default=False,
            ): bool,
        }
    )

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self.last_cycle_time = 20
        self.current_pixel = 0

    def on_activate(self, pixel_count):
        self.current_pixel = 0
        self.last_cycle_time = 20

    def config_updated(self, config):
        self.background_color = np.array(
            parse_color(self._config["background_color"]), dtype=float
        )
        self.pixel_color = np.array(
            parse_color(self._config["pixel_color"]), dtype=float
        )

    def effect_loop(self):
        pass_time = timeit.default_timer() - self.start_time
        cycle_time = pass_time % self._config["step_period"]

        if cycle_time < self.last_cycle_time:
            if self.current_pixel == 0 or not self._config["build_up"]:
                self.pixels[0 : self.pixel_count] = self.background_color

            self.pixels[self.current_pixel] = self.pixel_color

            self.current_pixel += 1

            if self.current_pixel == self.pixel_count:
                self.current_pixel = 0

        self.last_cycle_time = cycle_time