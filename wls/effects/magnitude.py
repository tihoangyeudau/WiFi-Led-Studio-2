import voluptuous as vol

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class MagnitudeAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Độ lớn"
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
                "frequency_range",
                description="Dải tần số để phát hiện nhịp",
                default="Thấp (nhịp+trầm)",
            ): vol.In(list(_power_funcs.keys())),
        }
    )

    def on_activate(self, pixel_count):
        self.magnitude = 0

    def config_updated(self, config):
        self.power_func = self._power_funcs[self._config["frequency_range"]]

    def audio_data_updated(self, data):
        self.magnitude = getattr(data, self.power_func)()
        super().gradient_magnitude_beat_power(data)

    def render(self):
        self.pixels = self.apply_gradient(self.magnitude) * 4
