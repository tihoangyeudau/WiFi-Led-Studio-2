import numpy as np
import voluptuous as vol

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BarAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Thanh"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "mode",
                description="Chọn từ các hoạt ảnh khác nhau",
                default="wipe",
            ): vol.In(list(["bounce", "wipe", "in-out"])),
            vol.Optional(
                "ease_method",
                description="Hồ sơ gia tốc của thanh",
                default="ease_out",
            ): vol.In(list(["ease_in_out", "ease_in", "ease_out", "linear"])),
            vol.Optional(
                "color_step",
                description="Số lượng màu thay đổi trên mỗi nhịp",
                default=0.125,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0625, max=0.5)),
            vol.Optional(
                "beat_skip",
                description="Bỏ qua nhịp chẵn hoặc lẻ",
                default="none",
            ): vol.In(list(["none", "odd", "even"])),
            vol.Optional(
                "beat_offset",
                description="Bù nhịp",
                default=0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.0, max=1.0)),
            vol.Optional(
                "skip_every",
                description="Nếu bỏ qua nhịp, hãy bỏ qua từng nhịp",
                default=1,
            ): vol.In(
                list([1, 2])
            ),  # if add 4, to skip every bar, a bit of extra work is required in audio.py
        }
    )

    def on_activate(self, pixel_count):
        self.beat_oscillator = 0
        self.beat_now = 0
        self.phase = 0
        self.color_idx = 0
        self.bar_len = 0.3
        self.last_beat = 0.0

    def audio_data_updated(self, data):
        # Run linear beat oscillator through easing method
        self.beat_oscillator = data.beat_oscillator()
        self.beat_oscillator = (
            self.beat_oscillator + self._config["beat_offset"]
        ) % 1.0
        # Only change phase when beat oscillator completes a cycle (near 0)
        # This prevents interrupting the bar movement mid-cycle
        if self.last_beat > 0.8 and self.beat_oscillator < 0.2:
            self.phase = 1 - self.phase  # flip flop 0->1, 1->0
            if self.phase == 0:
                # 8 colors, 4 beats to a bar
                self.color_idx += self._config["color_step"]
                self.color_idx = self.color_idx % 1  # loop back to zero
                
        self.last_beat = self.beat_oscillator

    def render(self):
        if self._config["ease_method"] == "ease_in_out":
            x = 0.5 * np.sin(np.pi * (self.beat_oscillator - 0.5)) + 0.5
        elif self._config["ease_method"] == "ease_in":
            x = self.beat_oscillator**2
        elif self._config["ease_method"] == "ease_out":
            x = -((self.beat_oscillator - 1) ** 2) + 1
        elif self._config["ease_method"] == "linear":
            x = self.beat_oscillator

        # Initialize default values
        bar_start = 0
        bar_end = 0

        # Compute position of bar start and stop
        if self._config["mode"] == "wipe":
            if self.phase == 0:
                bar_end = x
                bar_start = 0
            elif self.phase == 1:
                bar_end = 1
                bar_start = x

        elif self._config["mode"] == "bounce":
            x = x * (1 - self.bar_len)
            if self.phase == 0:
                bar_end = x + self.bar_len
                bar_start = x
            elif self.phase == 1:
                bar_end = 1 - x
                bar_start = 1 - (x + self.bar_len)

        elif self._config["mode"] == "in-out":
            if self.phase == 0:
                bar_end = x
                bar_start = 0
            elif self.phase == 1:
                bar_end = 1 - x
                bar_start = 0

        # Construct the bar
        color = self.get_gradient_color(self.color_idx)
        self.pixels = np.zeros(np.shape(self.pixels))
        
        # Ensure valid range
        start_pixel = max(0, min(int(self.pixel_count * bar_start), self.pixel_count))
        end_pixel = max(0, min(int(self.pixel_count * bar_end), self.pixel_count))
        
        if start_pixel < end_pixel and end_pixel <= self.pixel_count:
            self.pixels[start_pixel:end_pixel, :] = color
