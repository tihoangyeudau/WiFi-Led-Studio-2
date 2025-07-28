import numpy as np
import voluptuous as vol

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
                default=0.2,
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

        # Setup left and right sections
        self.output_left_length = self.led_mid
        self.output_left_max_index = self.output_left_length
        self.output_right_length = pixel_count - self.led_mid
        self.output_right_min_index = self.output_left_max_index

        self.output_left = np.zeros((3, self.output_left_length))
        self.output_right = np.zeros((3, self.output_right_length))

        # Direction and bar tracking
        self.current_direction = 1  # -1 = left, 1 = right
        self.bars_in_the_same_direction = 0
        self.current_bar_length_left = 0
        self.current_bar_length_right = 0
        self.bar_active = False

        # Beat detection
        self.beat_detected = False
        self.prev_beat_detected = False

    def config_updated(self, config):
        self.power_func = self._power_funcs[self._config["frequency_range"]]

    def audio_data_updated(self, data):
        # Get power from selected frequency range and detect beat edge
        current_power = getattr(data, self.power_func)()
        current_beat = current_power > self._config["beat_threshold"]

        self.beat_detected = current_beat and not self.prev_beat_detected
        self.prev_beat_detected = current_beat

    def render(self):
        steps = max(1, int(self._config["bar_speed"] * 3))

        # Add new bar only on beat detection and when no bar is active
        if self.beat_detected and not self.bar_active:
            self._add_new_bar(steps)

        # Process both sides
        self._process_left_side(steps)
        self._process_right_side(steps)

        # Combine outputs and set pixels
        output = np.zeros((3, self._pixel_count))
        output[:, :self.output_left_max_index] = self.output_left
        output[:, self.output_right_min_index:] = self.output_right
        self.pixels = output.T

        self._roll_gradient()

    def _process_left_side(self, steps):
        """Process left side movement (bars move left from center)"""
        if self.output_left_length == 0:
            return

        # Store last color for continuing bars
        last_color = self.output_left[:, -1]

        # Roll array left and clear new pixels
        self.output_left = np.roll(self.output_left, -steps, axis=1)
        clear_start = max(0, self.output_left_length - steps)
        self.output_left[:, clear_start:] = 0

        # Continue existing bar if needed
        if 0 < self.current_bar_length_left < self._config["bar_length"]:
            bar_length = self._config["bar_length"]
            missing_leds = min(steps, bar_length - self.current_bar_length_left)

            start_idx = self.output_left_length - steps
            end_idx = start_idx + missing_leds

            if start_idx >= 0 and end_idx <= self.output_left_length:
                self.output_left[:, start_idx:end_idx] = last_color[:, np.newaxis]

            self.current_bar_length_left += missing_leds
            if self.current_bar_length_left >= bar_length:
                self.current_bar_length_left = 0
                self.bar_active = False

    def _process_right_side(self, steps):
        """Process right side movement (bars move right from center)"""
        if self.output_right_length == 0:
            return

        # Store last color for continuing bars
        last_color = self.output_right[:, 0]

        # Roll array right and clear new pixels
        self.output_right = np.roll(self.output_right, steps, axis=1)
        self.output_right[:, :steps] = 0

        # Continue existing bar if needed
        if 0 < self.current_bar_length_right < self._config["bar_length"]:
            bar_length = self._config["bar_length"]
            missing_leds = min(steps, bar_length - self.current_bar_length_right)

            start_idx = max(0, steps - missing_leds)
            end_idx = steps

            if start_idx < end_idx:
                self.output_right[:, start_idx:end_idx] = last_color[:, np.newaxis]

            self.current_bar_length_right += missing_leds
            if self.current_bar_length_right >= bar_length:
                self.current_bar_length_right = 0
                self.bar_active = False

    def _add_new_bar(self, steps):
        """Add new bar when beat is detected"""
        color = self.get_gradient_color(0.5)
        bar_length = self._config["bar_length"]

        # Check direction change
        if self.bars_in_the_same_direction >= self._config["bars_in_same_direction"]:
            self.current_direction *= -1
            self.bars_in_the_same_direction = 0
        self.bars_in_the_same_direction += 1

        # Reset state and clear outputs
        self.current_bar_length_left = 0
        self.current_bar_length_right = 0
        self.output_left.fill(0)
        self.output_right.fill(0)
        self.bar_active = True

        # Add bar in current direction
        leds_to_show = min(steps, bar_length)

        if self.current_direction < 0:  # Left direction
            start_idx = max(0, self.output_left_length - steps)
            end_idx = min(self.output_left_length, start_idx + leds_to_show)
            if start_idx < end_idx:
                self.output_left[:, start_idx:end_idx] = color[:, np.newaxis]
            self.current_bar_length_left = leds_to_show
        else:  # Right direction
            start_idx = max(0, steps - leds_to_show)
            end_idx = min(self.output_right_length, steps)
            if start_idx < end_idx:
                self.output_right[:, start_idx:end_idx] = color[:, np.newaxis]
            self.current_bar_length_right = leds_to_show

