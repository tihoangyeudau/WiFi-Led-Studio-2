import numpy as np
import voluptuous as vol

from wls.effects.gradient import GradientEffect
from wls.effects.temporal import TemporalEffect


class FadeEffect(TemporalEffect, GradientEffect):
    """
    Fades through the colors of a gradient
    """

    NAME = "Phai màu"
    CATEGORY = "1. Hiệu ứng màu"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "speed",
                default=10,
                description="Tốc độ",
            ): vol.All(vol.Coerce(float), vol.Range(min=1, max=100)),
        }
    )

    def config_updated(self, config):
        self.idx = 0
        self.forward = True

    def on_activate(self, pixel_count):
        pass

    def effect_loop(self):
        self.idx += 0.0015
        if self.idx > 1:
            self.idx = 1
            self.forward = not self.forward
        self.idx = self.idx % 1

        if self.forward:
            i = self.idx
        else:
            i = 1 - self.idx

        color = self.get_gradient_color(i)
        self.pixels = np.tile(color, (self.pixel_count, 1))
