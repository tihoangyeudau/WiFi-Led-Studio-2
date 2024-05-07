import numpy as np
import voluptuous as vol

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BandsAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Băng tần"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "band_count", description="Số lượng băng tần", default=6
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=16)),
            vol.Optional(
                "align",
                description="Căn chỉnh các băng tần",
                default="left",
            ): vol.In(list(["left", "right", "invert", "center"])),
            vol.Optional(
                "mirror",
                description="Phản chiếu",
                default=False,
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

    def config_updated(self, config):
        self.bkg_color = np.array((0, 0, 0), dtype=float)

    def audio_data_updated(self, data):
        # Grab the filtered melbank
        self.r = self.melbank(filtered=True, size=self.pixel_count)

    def render(self):
        bands_active = min(self._config["band_count"], self.pixel_count)
        out = np.tile(self.r, (3, 1)).T
        np.clip(out, 0, 1, out=out)
        out_split = np.array_split(out, bands_active, axis=0)
        for i in range(bands_active):
            band_width = len(out_split[i])
            color = self.get_gradient_color(i / bands_active)
            vol = int(out_split[i].max() * band_width)  # length (vol) of band
            out_split[i][:] = self.bkg_color
            if vol:
                out_split[i][:vol] = color
            if self._config["align"] == "center":
                out_split[i] = np.roll(
                    out_split[i], (band_width - vol) // 2, axis=0
                )
            elif self._config["align"] == "invert":
                out_split[i] = np.roll(out_split[i], -vol // 2, axis=0)
            elif self._config["align"] == "right":
                out_split[i] = np.flip(out_split[i], axis=0)
            elif self._config["align"] == "left":
                pass

        self.pixels = np.vstack(out_split)
        self._roll_gradient()
