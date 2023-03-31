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


class MetroEffect(TemporalEffect):
    NAME = "Tàu điện"
    CATEGORY = "Chuẩn đoán"
    HIDDEN_KEYS = ["speed", "background_brightness", "blur", "mirror"]

    start_time = timeit.default_timer()

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "speed",
                default=20.0,
                description="Khóa tại 20 fps",
            ): vol.All(vol.Coerce(float), vol.Range(min=20, max=20)),
            vol.Optional(
                "pulse_period",
                description="Thời gian giữa các lần nháy tính bằng giây",
                default=1,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional(
                "pulse_ratio",
                description="Tỷ lệ flash thành trống",
                default=0.3,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.9)),
            vol.Optional(
                "steps",
                description="Các bước phân chia mẫu để lặp",
                default=4,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=6)),
            vol.Optional(
                "background_color",
                description="Màu nền",
                default="#000000",
            ): validate_color,
            vol.Optional(
                "flash_color",
                description="Màu chớp",
                default="#FFFFFF",
            ): validate_color,
        }
    )

    def __init__(self, wls, config):
        super().__init__(wls, config)
        self.was_flash = False

    def on_activate(self, pixel_count):
        pass

    def config_updated(self, config):
        self.background_color = np.array(
            parse_color(self._config["background_color"]), dtype=float
        )
        self.flash_color = np.array(
            parse_color(self._config["flash_color"]), dtype=float
        )

        self.cycle_threshold = self._config["pulse_period"] * (
            self._config["pulse_ratio"]
        )

    def effect_loop(self):
        pass_time = timeit.default_timer() - self.start_time
        cycle_time = pass_time % self._config["pulse_period"]

        if cycle_time > self.cycle_threshold:
            if self.was_flash:
                self.pixels[0 : self.pixel_count] = self.background_color
                self.was_flash = False
        else:
            if not self.was_flash:
                step_count = (
                    int(pass_time / self._config["pulse_period"])
                    % self._config["steps"]
                )
                if step_count == 0:
                    self.pixels[0 : self.pixel_count] = self.flash_color
                else:
                    step_div = pow(2, step_count - 1)
                    chunk = int(self.pixel_count / (step_div))
                    for blocks in range(0, step_div):
                        start_pixel = blocks * chunk
                        end_pixel = start_pixel + int(chunk / 2)
                        self.pixels[
                            start_pixel : end_pixel - 1
                        ] = self.flash_color
                self.was_flash = True