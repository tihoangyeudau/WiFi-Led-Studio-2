import numpy as np
import voluptuous as vol

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BlocksAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Khối"
    CATEGORY = "2D"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "block_count",
                description="Số màu khối",
                default=4,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10))
        }
    )

    def on_activate(self, pixel_count):
        self.r = np.zeros(pixel_count)

    def audio_data_updated(self, data):
        # Grab the filtered melbank
        self.r = self.melbank(filtered=True, size=self.pixel_count) * 2

    def render(self):
        out = np.tile(self.r, (3, 1))
        out_split = np.array_split(out, self._config["block_count"], axis=1)
        for i in range(self._config["block_count"]):
            color = self.get_gradient_color(i / self._config["block_count"])[
                :, np.newaxis
            ]
            out_split[i] = np.multiply(
                out_split[i], (out_split[i].max() * color)
            )

        self.pixels = np.hstack(out_split).T
