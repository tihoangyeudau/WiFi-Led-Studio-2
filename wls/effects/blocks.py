import numpy as np
import voluptuous as vol

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BlocksAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Khối"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "block_count",
                description="Số màu khối",
                default=5,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional(
                "mirror",
                description="Phản chiếu",
                default=True,
            ): bool,
            vol.Optional(
                "gradient_roll",
                description="Tốc độ dải mầu",
                default=0.4,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
        }
    )

    def on_activate(self, pixel_count):
        self.r = np.zeros(pixel_count)

    def audio_data_updated(self, data):
        # Grab the filtered melbank
        self.r = self.melbank(filtered=True, size=self.pixel_count)

    def render(self):
        blocks_active = min(self._config["block_count"], self.pixel_count)

        out = np.tile(self.r, (3, 1))
        out_split = np.array_split(out, blocks_active, axis=1)
        for i in range(blocks_active):
            color = self.get_gradient_color(i / blocks_active)[:, np.newaxis]
            out_split[i] = np.multiply(
                out_split[i], (out_split[i].max() * color)
            )

        self.pixels = np.hstack(out_split).T
        self._roll_gradient()
