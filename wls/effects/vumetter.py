import numpy as np
import voluptuous as vol

from wls.color import parse_color, validate_color
from wls.effects.audio import AudioReactiveEffect


class VuMeterAudioEffect(AudioReactiveEffect):
    NAME = "Cột âm lượng"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"
    HIDDEN_KEYS = ["background_color", "background_brightness", "blur"]

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "peak_decay",
                description="Bộ lọc phân rã được áp dụng cho khối lượng thô để theo dõi mức cao nhất, 0 là Không có",
                default=0.1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.01, max=0.3)),
            vol.Optional(
                "color_min",
                description="Màu sắc của điểm cắt âm lượng tối thiểu",
                default="#0000FF",
            ): validate_color,
            vol.Optional(
                "color_max",
                description="Màu của cảnh báo âm lượng tối đa",
                default="#FF0000",
            ): validate_color,
            vol.Optional(
                "color_mid",
                description="Màu sắc của phạm vi âm lượng trung bình",
                default="#00FF00",
            ): validate_color,
            vol.Optional(
                "color_peak",
                description="Màu của đỉnh",
                default="#FFFFFF",
            ): validate_color,
            vol.Optional(
                "peak_percent",
                description="% kích thước đỉnh theo thể tích đã lọc",
                default=1.0,
            ): vol.All(vol.Coerce(int), vol.Range(min=0, max=5)),
            vol.Optional(
                "max_volume",
                description="Giới hạn cắt để cảnh báo âm lượng tối đa",
                default=0.8,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
        }
    )

    def on_activate(self, pixel_count):
        pass

    def config_updated(self, config):
        self.volume_peak_filter = self.create_filter(
            alpha_decay=self._config["peak_decay"], alpha_rise=0.99
        )
        self.volume_min_peak_filter = self.create_filter(
            alpha_decay=self._config["peak_decay"], alpha_rise=0.99
        )

        self.color_peak = parse_color(self._config["color_peak"])
        self.color_min = parse_color(self._config["color_min"])
        self.color_max = parse_color(self._config["color_max"])
        self.color_mid = parse_color(self._config["color_mid"])
        self.peak_percent = self._config["peak_percent"]
        self.vol_max = 0.8
        self.volume = 0
        self.volume_peak = 0
        self.volume_min_peak = 0
        self.volume_min = 0

    def audio_data_updated(self, data):
        # grab the raw volume from the audio driver
        self.volume = max(0, min(1, self.audio.volume(filtered=False)))
        self.volume_peak = self.volume_peak_filter.update(self.volume)
        self.volume_min_peak = self.volume_min_peak_filter.update(
            1 - self.volume
        )
        self.volume_min = 0.2

    def render(self):
        self.pixels = np.zeros(np.shape(self.pixels))

        volume = int(self.pixel_count * self.volume)
        volume_min = min(
            int(self.pixel_count * self.volume_min), self.pixel_count
        )
        volume_max = min(
            int(self.pixel_count * self.vol_max), self.pixel_count
        )

        self.pixels[0 : min(volume_min, volume)] = self.color_min
        if volume > volume_min:
            self.pixels[volume_min : min(volume, volume_max)] = self.color_mid
        if volume > volume_max:
            self.pixels[volume_max:volume] = self.color_max
        if self.peak_percent > 0:
            peak_start = min(
                int(self.pixel_count * self.volume_peak), self.pixel_count
            )
            peak_end = min(
                peak_start
                + int(self.peak_percent * (self.pixel_count / 100.0)),
                self.pixel_count,
            )
            self.pixels[peak_start:peak_end] = self.color_peak
            min_peak_start = max(
                0,
                min(
                    int(self.pixel_count * (1 - self.volume_min_peak)),
                    self.pixel_count,
                ),
            )
            min_peak_end = max(
                0,
                min(
                    min_peak_start
                    - int(self.peak_percent * (self.pixel_count / 100.0)),
                    self.pixel_count,
                ),
            )
            self.pixels[min_peak_end:min_peak_start] = self.color_peak