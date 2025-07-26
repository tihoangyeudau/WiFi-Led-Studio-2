import numpy as np
import voluptuous as vol

from wls.color import parse_color, validate_color
from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BarsAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Thanh phổ"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "resolution",
                description="Độ phân giải (số thanh)",
                default=8,
            ): vol.All(vol.Coerce(int), vol.Range(min=4, max=32)),
            vol.Optional(
                "sensitivity",
                description="Độ nhạy",
                default=1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=2.0)),
            vol.Optional(
                "mirror",
                description="Phản chiếu",
                default=False,
            ): bool,
            vol.Optional(
                "gradient_roll",
                description="Tốc độ dải mầu",
                default=0.1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
        }
    )

    def on_activate(self, pixel_count):
        self.prev_spectrum = np.zeros(self.pixel_count // 2)
        self.current_melbank = np.zeros(self.pixel_count // 2)

    def config_updated(self, config):
        # No special color setup needed - using GradientEffect's gradient system
        pass

    def audio_data_updated(self, data):
        # Get melbank data
        melbank = self.melbank(filtered=False, size=self.pixel_count // 2)

        if melbank is None or len(melbank) == 0:
            return

        # Apply sensitivity
        melbank = melbank * self._config["sensitivity"]

        # Store for processing
        self.current_melbank = np.clip(melbank, 0, 1)

    def render(self):
        if not hasattr(self, 'current_melbank'):
            return

        # Get resolution (number of blocks)
        resolution = self._config.get("resolution", 8)

        # Process melbank data like original effect_bars.py
        y = np.copy(self.current_melbank)

        # Duplicate values to match original: [j for i in zip(r, r) for j in i]
        r = np.array([j for i in zip(y, y) for j in i])

        # Split into resolution chunks and get max values
        max_values = np.array([max(chunk) if len(chunk) > 0 else 0
                              for chunk in np.array_split(r, resolution)])
        max_values = np.clip(max_values, 0, 1)

        # Create output array
        output = np.zeros((3, self.pixel_count))

        # Split pixel array into blocks (not bars!)
        pixel_chunks = np.array_split(np.arange(self.pixel_count), resolution)

        # Assign each block a color and brightness
        for i, chunk_indices in enumerate(pixel_chunks):
            if len(chunk_indices) == 0:
                continue

            # Get gradient color for this block position
            gradient_pos = i / (resolution - 1) if resolution > 1 else 0
            color = self.get_gradient_color(gradient_pos)

            # Apply brightness based on audio data to entire block
            brightness = max_values[i] if i < len(max_values) else 0

            # Fill entire block with color * brightness
            for idx in chunk_indices:
                output[0, idx] = color[0] * brightness
                output[1, idx] = color[1] * brightness
                output[2, idx] = color[2] * brightness

        # Apply mirror effect if enabled
        if self._config["mirror"]:
            output = self._apply_mirror(output)

        # Set pixels and roll gradient
        self.pixels = output.T
        self._roll_gradient()

    def _apply_mirror(self, array):
        """Apply mirror effect"""
        mid = self.pixel_count // 2
        left_half = array[:, :mid]
        mirrored_array = array.copy()
        mirrored_array[:, mid:] = np.fliplr(left_half)
        return mirrored_array