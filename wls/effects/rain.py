from random import randint

import numpy as np
import voluptuous as vol

from wls.color import parse_color, validate_color
from wls.effects.audio import AudioReactiveEffect
from wls.effects.droplets import DROPLET_NAMES, load_droplet


class RainAudioEffect(AudioReactiveEffect):
    NAME = "Mưa"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "mirror",
                description="Phản chiếu",
                default=True,
            ): bool,
            # TODO drops should be controlled by some sort of effectlet class,
            # which will provide a list of available drop names rather than just
            # this static range
            vol.Optional(
                "lows_color",
                description="Màu âm trầm",
                default="white",
            ): validate_color,
            vol.Optional(
                "pulse_strip",
                description="Xung toàn bộ dải theo nhịp",
                default="Tắt",
            ): vol.In(["Tắt", "Trầm", "Trung", "Cao"]),
            vol.Optional(
                "mids_color",
                description="Màu của âm trung",
                default="red",
            ): validate_color,
            vol.Optional(
                "high_color",
                description="Màu của âm cao",
                default="blue",
            ): validate_color,
            vol.Optional(
                "lows_sensitivity",
                description="Độ nhậy âm trầm",
                default=0.05,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.03, max=1)),
            vol.Optional(
                "mids_sensitivity",
                description="Độ nhậy âm trung",
                default=0.2,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.03, max=1)),
            vol.Optional(
                "high_sensitivity",
                description="Độ nhậy âm bổng",
                default=0.1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.03, max=1)),
            vol.Optional(
                "raindrop_animation",
                description="Kiểu hoạt ảnh giọt nước",
                default=DROPLET_NAMES[0],
            ): vol.In(DROPLET_NAMES),
            vol.Optional(
                "trigger_cooldown",
                description="Thời gian chờ giữa các lần kích hoạt (giây)",
                default=0.4,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.05, max=0.5)),
        }
    )

    def on_activate(self, pixel_count):
        self.drop_frames = np.zeros(self.pixel_count, dtype=int)
        self.drop_colors = np.zeros((3, self.pixel_count))
        self.pulse_pixels = np.zeros((self.pixel_count, 3))
        # Cooldown timers to prevent too frequent triggers
        self.last_trigger_time = [0.0, 0.0, 0.0]  # for lows, mids, highs

    def config_updated(self, config):
        self.drop_animation = load_droplet(config["raindrop_animation"])

        self.n_frames, self.frame_width = np.shape(self.drop_animation)
        self.frame_centre_index = self.frame_width // 2
        self.frame_side_lengths = self.frame_centre_index - 1

        self.intensity_filter = self.create_filter(
            alpha_decay=0.3, alpha_rise=0.95
        )
        self.filtered_intensities = np.zeros(3)

    def new_drop(self, location, color):
        """
        Add a new drop animation
        TODO (?) this method overwrites a running drop animation in the same location
        would need a significant restructure to fix
        """
        self.drop_frames[location] = 1
        self.drop_colors[:, location] = color

    def update_drop_frames(self):
        # Set any drops at final frame back to 0 and remove color data
        finished_drops = self.drop_frames >= self.n_frames - 1
        self.drop_frames[finished_drops] = 0
        self.drop_colors[:, finished_drops] = 0
        # Add one to any running frames
        self.drop_frames[self.drop_frames > 0] += 1

    def render(self):
        """
        Get colored pixel data of all drops overlaid
        """
        # 2d array containing color intensity data
        overlaid_frames = np.zeros((3, self.pixel_count + self.frame_width))
        # Indexes of active drop animations
        drop_indices = np.flatnonzero(self.drop_frames)
        # TODO vectorize this to remove for loop
        for index in drop_indices:
            if self.drop_frames[index] >= len(self.drop_animation):
                continue
            colored_frame = [
                self.drop_animation[self.drop_frames[index]]
                * self.drop_colors[color, index]
                for color in range(3)
            ]
            overlaid_frames[
                :, index : index + self.frame_width
            ] += colored_frame

        # Clip values to prevent overflow - this is crucial for smooth animation!
        np.clip(overlaid_frames, 0, 255, out=overlaid_frames)

        self.pixels = overlaid_frames[
            :,
            self.frame_side_lengths : self.frame_side_lengths
            + self.pixel_count,
        ].T
        self.pixels += self.pulse_pixels
        # Decay the pulse pixels
        self.pulse_pixels = (self.pulse_pixels * 9) // 10

    def strip_pulse(self, color):
        """
        Set the pulse pixels to a color
        This color decays over time in render()

        Args:
            color: The color to pulse the strip
        """
        self.pulse_pixels = np.array([color])

    def audio_data_updated(self, data):
        import time
        current_time = time.time()

        # Calculate the low, mids, and high indexes scaling based on the pixel
        # count - using mean like the old version for better sensitivity
        melbank_data = self.melbank_thirds()
        intensities = np.array([
            np.mean(melbank_data[0]),  # lows
            np.mean(melbank_data[1]),  # mids
            np.mean(melbank_data[2]),  # highs
        ])

        self.update_drop_frames()

        # Check lows with cooldown
        if (
            intensities[0] - self.filtered_intensities[0] > self._config["lows_sensitivity"]
            and current_time - self.last_trigger_time[0] > self._config["trigger_cooldown"]
        ):
            self.last_trigger_time[0] = current_time
            if self._config["pulse_strip"] == "Trầm":
                self.strip_pulse(parse_color(self._config["lows_color"]))
            else:
                self.new_drop(
                    randint(0, self.pixel_count - 1),
                    parse_color(self._config["lows_color"]),
                )

        # Check mids with cooldown
        if (
            intensities[1] - self.filtered_intensities[1] > self._config["mids_sensitivity"]
            and current_time - self.last_trigger_time[1] > self._config["trigger_cooldown"]
        ):
            self.last_trigger_time[1] = current_time
            if self._config["pulse_strip"] == "Trung":
                self.strip_pulse(parse_color(self._config["mids_color"]))
            else:
                self.new_drop(
                    randint(0, self.pixel_count - 1),
                    parse_color(self._config["mids_color"]),
                )

        # Check highs with cooldown
        if (
            intensities[2] - self.filtered_intensities[2] > self._config["high_sensitivity"]
            and current_time - self.last_trigger_time[2] > self._config["trigger_cooldown"]
        ):
            self.last_trigger_time[2] = current_time
            if self._config["pulse_strip"] == "Cao":
                self.strip_pulse(parse_color(self._config["high_color"]))
            else:
                self.new_drop(
                    randint(0, self.pixel_count - 1),
                    parse_color(self._config["high_color"]),
                )

        self.filtered_intensities = self.intensity_filter.update(intensities)