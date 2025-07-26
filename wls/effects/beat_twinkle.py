import numpy as np
import voluptuous as vol
import random

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BeatTwinkleAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Lấp lánh"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "star_length",
                description="Độ dài ngôi sao",
                default=5,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=20)),
            vol.Optional(
                "decay",
                description="Độ mờ dần",
                default=0.85,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.99)),
            vol.Optional(
                "max_stars",
                description="Số ngôi sao tối đa cùng lúc",
                default=3,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional(
                "random_color",
                description="Màu ngẫu nhiên cho mỗi ngôi sao",
                default=True,
            ): bool,
        }
    )

    def on_activate(self, pixel_count):
        self.prev_output = np.zeros((3, pixel_count))
        self.beat_detected = False

        # Beat detection variables
        self.beat_history = []
        self.last_beat_time = 0

    def config_updated(self, config):
        pass

    def audio_data_updated(self, data):
        # Use WLS2's built-in beat detection
        self.beat_detected = data.volume_beat_now()

    def render(self):
        # Apply decay to previous output
        output = self.prev_output * self._config["decay"]

        # Add new twinkles ONLY on beat detection
        if self.beat_detected:
            self._add_twinkle_stars(output)

        # Store for next frame
        self.prev_output = output.copy()

        # Set pixels
        self.pixels = output.T

        # Roll gradient for color changes
        self._roll_gradient()

    def _add_twinkle_stars(self, output):
        """Add twinkle stars when beat is detected"""
        star_length = min(self._config["star_length"], self.pixel_count)
        max_stars = self._config["max_stars"]

        # Add multiple stars for stronger effect
        num_stars = random.randint(1, max_stars)

        for _ in range(num_stars):
            # Calculate valid start position
            max_start = self.pixel_count - star_length
            if max_start <= 0:
                star_start = 0
                star_length = self.pixel_count
            else:
                star_start = random.randint(0, max_start)

            # Get color for this star
            color = self._get_star_color()

            # Add star to output
            star_end = star_start + star_length
            output[0][star_start:star_end] = np.maximum(
                output[0][star_start:star_end],
                color[0]
            )
            output[1][star_start:star_end] = np.maximum(
                output[1][star_start:star_end],
                color[1]
            )
            output[2][star_start:star_end] = np.maximum(
                output[2][star_start:star_end],
                color[2]
            )

    def _get_star_color(self):
        """Get color for a new star from gradient"""
        if self._config["random_color"]:
            # Random position in gradient for variety (like old behavior)
            gradient_position = random.uniform(0.0, 1.0)
        else:
            # Fixed position in gradient (like DirectionChanger)
            # Gradient roll will automatically change colors over time
            gradient_position = 0.5

        color = self.get_gradient_color(gradient_position)

        # Add some brightness variation
        brightness = random.uniform(0.7, 1.0)
        return color * brightness