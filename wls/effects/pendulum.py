import numpy as np
import voluptuous as vol

from wls.color import validate_gradient
from wls.effects.temporal import TemporalEffect
from wls.effects.gradient import GradientEffect


class PendulumEffect(TemporalEffect, GradientEffect):

    NAME = "Con lắc"
    CATEGORY = "1. Hiệu ứng màu"

    def __init__(self, wls, config):
        super().__init__(wls, config)
        # Initialize state variables
        self.speed_counter = 0
        self.current_direction = True
        self.current_position = 0

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "gradient",
                description="Dải màu gradient",
                default="linear-gradient(90deg, rgb(255, 0, 0) 0%, rgb(255, 120, 0) 14%, rgb(255, 200, 0) 28%, rgb(0, 255, 0) 42%, rgb(0, 199, 140) 56%, rgb(0, 0, 255) 70%, rgb(128, 0, 128) 84%, rgb(255, 0, 178) 98%)",
            ): validate_gradient,
            vol.Optional(
                "gradient_roll",
                description="Tốc độ cuộn gradient",
                default=0.5,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
            vol.Optional(
                "beat_speed",
                description="Tốc độ cuộn chuyển màu được điều chỉnh dựa trên cường độ nhịp âm thanh",
                default=False,
            ): bool,
            vol.Optional(
                "pendulum_length",
                description="Độ dài con lắc",
                default=15,
            ): vol.All(vol.Coerce(int), vol.Range(min=2, max=50)),
            vol.Optional(
                "speed",
                description="Tốc độ con lắc",
                default=3.0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=10.0)),
            vol.Optional(
                "trail_effect",
                description="Hiệu ứng đuôi",
                default=False,
            ): bool,
            vol.Optional(
                "trail_decay",
                description="Độ mờ dần của đuôi",
                default=0.8,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.99)),
        }
    )

    def on_activate(self, pixel_count):
        # Pendulum state
        self.current_direction = True  # True = right, False = left
        # Start at left boundary (center-based)
        half_length = self._config["pendulum_length"] // 2
        self.current_position = half_length
        self.speed_counter = 0

        # Trail effect
        self.trail_array = np.zeros((3, pixel_count))

    def config_updated(self, config):
        # Invalidate gradient when config changes
        super().config_updated(config)

    def effect_loop(self):
        """Main effect loop called by TemporalEffect"""
        # Calculate movement steps
        steps = self._get_roll_steps(self._config["speed"])

        # Handle trail decay if enabled
        if self._config["trail_effect"]:
            # Apply decay to trail
            self.trail_array *= self._config["trail_decay"]

        # Calculate pendulum boundaries for bounce detection
        half_length = self._config["pendulum_length"] // 2
        left_boundary = half_length
        right_boundary = self.pixel_count - 1 - half_length

        # Move pendulum center position
        if self.current_direction:  # Moving right
            self.current_position = min(self.current_position + steps, right_boundary)

            # Check for direction change at right boundary
            if self.current_position >= right_boundary:
                self.current_position = right_boundary
                self.current_direction = False

        else:  # Moving left
            self.current_position = max(self.current_position - steps, left_boundary)

            # Check for direction change at left boundary
            if self.current_position <= left_boundary:
                self.current_position = left_boundary
                self.current_direction = True

        # Calculate pendulum position (center-based)
        start_pos = max(0, self.current_position - half_length)
        end_pos = min(self.pixel_count, self.current_position + half_length + 1)

        # Create pendulum mask
        pendulum_mask = np.zeros(self.pixel_count)
        pendulum_mask[start_pos:end_pos] = 1.0

        # Apply gradient to pendulum
        pendulum_pixels = self.apply_gradient(pendulum_mask)

        # Handle trail effect
        if self._config["trail_effect"]:
            # Convert pendulum pixels to (3, pixel_count) format for trail
            current_pendulum = pendulum_pixels.T

            # Combine with trail using maximum (brightest pixel wins)
            self.trail_array = np.maximum(self.trail_array, current_pendulum)

            # Convert back to (pixel_count, 3) format for output
            self.pixels = self.trail_array.T
        else:
            # No trail, just use pendulum pixels directly
            self.pixels = pendulum_pixels

        # Return speed modifier for TemporalEffect
        return 1.0

    def _get_roll_steps(self, current_speed):
        """Calculate movement steps based on speed"""
        max_counter = 1
        steps = 0

        self.speed_counter += current_speed

        if self.speed_counter > max_counter:
            self.speed_counter = 0

            if (max_counter / current_speed) < 1:
                steps = int(1 / (max_counter / current_speed))
            else:
                steps = 1
        else:
            steps = 0

        return steps