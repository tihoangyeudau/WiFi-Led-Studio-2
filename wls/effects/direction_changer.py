import numpy as np
import voluptuous as vol
import random


from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class DirectionChangerAudioEffect(GradientEffect, AudioReactiveEffect):

    NAME = "Đảo chiều"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

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
                "bar_length",
                description="Độ dài thanh",
                default=12,
            ): vol.All(vol.Coerce(int), vol.Range(min=2, max=30)),
            vol.Optional(
                "bar_speed",
                description="Tốc độ thanh",
                default=1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=3.0)),
            vol.Optional(
                "bars_in_same_direction",
                description="Số thanh cùng hướng trước khi đổi",
                default=1,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
            vol.Optional(
                "frequency_range",
                description="Dải tần số để phát hiện nhịp",
                default="Thấp (nhịp+trầm)",
            ): vol.In(list(_power_funcs.keys())),
            vol.Optional(
                "beat_threshold",
                description="Ngưỡng phát hiện nhịp",
                default=0.3,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
            vol.Optional(
                "gradient_roll",
                description="Tốc độ dải mầu",
                default=1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
        }
    )

    def on_activate(self, pixel_count):
        self._pixel_count = pixel_count
        self.led_mid = pixel_count // 2

        # Setup left and right sections like original
        self.output_left_length = self.led_mid
        self.output_left_min_index = 0
        self.output_left_max_index = self.output_left_length

        self.output_right_length = pixel_count - self.led_mid
        self.output_right_min_index = self.output_left_max_index
        self.output_right_max_index = self.output_right_min_index + self.output_right_length

        self.output_left = np.zeros((3, self.output_left_length))
        self.output_right = np.zeros((3, self.output_right_length))

        # Direction: -1 = left, 1 = right
        self.current_direction = 1
        self.bars_in_the_same_direction = 0
        self.current_bar_length_left = 0
        self.current_bar_length_right = 0

        self.beat_detected = False
        self.current_power = 0.0
        self.prev_beat_detected = False  # Track previous beat state

    def config_updated(self, config):
        self.power_func = self._power_funcs[self._config["frequency_range"]]

    def audio_data_updated(self, data):
        # Get power from selected frequency range
        self.current_power = getattr(data, self.power_func)()
        # Detect beat based on power threshold
        current_beat = self.current_power > self._config["beat_threshold"]
        
        # Only trigger on beat edge (from no beat to beat)
        self.beat_detected = current_beat and not self.prev_beat_detected
        self.prev_beat_detected = current_beat

    def render(self):
        # Calculate movement steps based on bar_speed
        steps = max(1, int(self._config["bar_speed"] * 3))  # Convert speed to steps

        # Process left side (bars move left from center)
        self._process_left_side(steps)

        # Process right side (bars move right from center)
        self._process_right_side(steps)

        # Add new bar ONLY on beat detection (like original)
        if self.beat_detected:
            self._add_new_bar(steps)

        # Combine left and right outputs
        output = np.zeros((3, self._pixel_count))
        output[:, :self.output_left_max_index] = self.output_left
        output[:, self.output_right_min_index:] = self.output_right

        # Set pixels
        self.pixels = output.T

        # Roll gradient for color changes
        self._roll_gradient()

    def _process_left_side(self, steps):
        """Process left side movement (bars move left from center)"""
        # Store last color for continuing bars
        last_color = [
            self.output_left[0][-1] if self.output_left_length > 0 else 0,
            self.output_left[1][-1] if self.output_left_length > 0 else 0,
            self.output_left[2][-1] if self.output_left_length > 0 else 0
        ]

        # Roll array left (negative direction)
        self.output_left = np.roll(self.output_left, -steps, axis=1)

        # Clear rolled pixels with black
        left_index = self.output_left_length - steps
        if left_index >= 0:
            self.output_left[:, left_index:] = 0

        # Continue existing bar if needed
        if 0 < self.current_bar_length_left < self._config["bar_length"]:
            bar_length = self._config["bar_length"]
            missing_leds = min(steps, bar_length - self.current_bar_length_left)

            left_index = self.output_left_length - steps
            right_index = left_index + missing_leds

            if left_index >= 0 and right_index <= self.output_left_length:
                self.output_left[0][left_index:right_index] = last_color[0]
                self.output_left[1][left_index:right_index] = last_color[1]
                self.output_left[2][left_index:right_index] = last_color[2]

            self.current_bar_length_left += missing_leds
            if self.current_bar_length_left >= bar_length:
                self.current_bar_length_left = 0

    def _process_right_side(self, steps):
        """Process right side movement (bars move right from center)"""
        # Store last color for continuing bars
        last_color = [
            self.output_right[0][0] if self.output_right_length > 0 else 0,
            self.output_right[1][0] if self.output_right_length > 0 else 0,
            self.output_right[2][0] if self.output_right_length > 0 else 0
        ]

        # Roll array right (positive direction)
        self.output_right = np.roll(self.output_right, steps, axis=1)

        # Clear rolled pixels with black
        self.output_right[:, :steps] = 0

        # Continue existing bar if needed
        if 0 < self.current_bar_length_right < self._config["bar_length"]:
            bar_length = self._config["bar_length"]
            missing_leds = min(steps, bar_length - self.current_bar_length_right)

            left_index = max(0, steps - missing_leds)
            right_index = steps

            if left_index < right_index:
                self.output_right[0][left_index:right_index] = last_color[0]
                self.output_right[1][left_index:right_index] = last_color[1]
                self.output_right[2][left_index:right_index] = last_color[2]

            self.current_bar_length_right += missing_leds
            if self.current_bar_length_right >= bar_length:
                self.current_bar_length_right = 0

    def _get_bar_color(self):
        """Get color for new bar from gradient"""
        # Get color from a fixed position in gradient (0.5 = center)
        # Gradient roll will automatically change colors over time
        return self.get_gradient_color(0.5)



    def _add_new_bar(self, steps):
        """Add new bar when beat is detected"""
        # Get color for new bar
        color = self._get_bar_color()
        bar_length = self._config["bar_length"]

        # Check if we need to change direction
        if self.bars_in_the_same_direction >= self._config["bars_in_same_direction"]:
            self.current_direction *= -1
            self.bars_in_the_same_direction = 0

        self.bars_in_the_same_direction += 1

        # Add bar in current direction
        if self.current_direction < 0:  # Left direction
            leds_to_show = min(steps, bar_length)
            start_idx = max(0, self.output_left_length - steps)
            end_idx = min(self.output_left_length, start_idx + leds_to_show)

            if start_idx < end_idx:
                self.output_left[0][start_idx:end_idx] = color[0]
                self.output_left[1][start_idx:end_idx] = color[1]
                self.output_left[2][start_idx:end_idx] = color[2]

            self.current_bar_length_left = leds_to_show

        else:  # Right direction
            leds_to_show = min(steps, bar_length)
            start_idx = max(0, steps - leds_to_show)
            end_idx = min(self.output_right_length, steps)

            if start_idx < end_idx:
                self.output_right[0][start_idx:end_idx] = color[0]
                self.output_right[1][start_idx:end_idx] = color[1]
                self.output_right[2][start_idx:end_idx] = color[2]

            self.current_bar_length_right = leds_to_show

