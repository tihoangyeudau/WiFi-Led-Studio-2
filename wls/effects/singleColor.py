import numpy as np
import voluptuous as vol

from wls.color import parse_color, validate_color
from wls.effects.modulate import ModulateEffect
from wls.effects.temporal import TemporalEffect


class SingleColorEffect(TemporalEffect, ModulateEffect):

    NAME = "Màu đơn"
    CATEGORY = "Không nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "color", description="Màu", default="#FF0000"
            ): validate_color,
        },
    )

    def config_updated(self, config):
        self.color = np.array(parse_color(self._config["color"]), dtype=float)

    def effect_loop(self):
        color_array = np.tile(self.color, (self.pixel_count, 1))
        self.pixels = self.modulate(color_array)
