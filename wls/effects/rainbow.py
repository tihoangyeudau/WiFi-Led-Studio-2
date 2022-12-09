import voluptuous as vol

from wls.effects import fill_rainbow
from wls.effects.temporal import TemporalEffect


class RainbowEffect(TemporalEffect):

    NAME = "Cầu vồng"
    CATEGORY = "Không nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
            "speed",
                description="Tốc độ",
                default=3,
            ): vol.All(vol.Coerce(float), vol.Range(min=1, max=100)),
            vol.Optional(
                "frequency",
                description="Độ phân giải của cầu vồng",
                default=0.8,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10)),
        }
    )

    _hue = 0.1

    def on_activate(self, pixel_count):
        pass

    def effect_loop(self):
        hue_delta = self._config["frequency"] / self.pixel_count
        self.pixels = fill_rainbow(self.pixels, self._hue, hue_delta)

        self._hue = self._hue + 0.01
