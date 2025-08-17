import numpy as np
import voluptuous as vol
import asyncio

from wls.color import parse_color, validate_color
from wls.effects.temporal import TemporalEffect
from wls.utils import async_fire_and_forget

class MoRongManEffect(TemporalEffect):
    """
    Effect "Mở rộng màn" - Gọi hàm stop_aw từ core khi được kích hoạt
    """

    NAME = "Mở rộng màn"
    CATEGORY = "3. Chuyển dổi"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "color",
                description="Màu hiệu ứng",
                default="#FF0000"
            ): validate_color,
            vol.Optional(
                "speed",
                description="Tốc độ",
                default=10,
            ): vol.All(vol.Coerce(float), vol.Range(min=1, max=100)),
            vol.Optional(
                "auto_trigger",
                description="Tự động kích hoạt stop_aw",
                default=True,
            ): bool,
        }
    )

    def config_updated(self, config):
        self.color = np.array(parse_color(self._config["color"]), dtype=float)
        self.triggered = False
        self.frame_count = 0

    def on_activate(self, pixel_count):
        """Được gọi khi effect được kích hoạt"""
        self.triggered = False
        self.frame_count = 0

        # Nếu auto_trigger được bật, gọi stop_aw sau một delay nhỏ để đảm bảo API response được gửi
        if self._config.get("auto_trigger", True):
            self._schedule_stop_aw()

    def _schedule_stop_aw(self):
        """Lên lịch gọi stop_aw sau một delay nhỏ"""
        if hasattr(self._wls, 'loop') and self._wls.loop:
            async_fire_and_forget(self._delayed_stop_aw(), self._wls.loop)
        else:
            # Fallback nếu không có loop
            self._trigger_stop_aw()

    async def _delayed_stop_aw(self):
        """Gọi stop_aw sau delay để đảm bảo API response được gửi"""
        # Delay 1 giây để đảm bảo API response được gửi
        await asyncio.sleep(1.0)
        self._trigger_stop_aw()

    def _trigger_stop_aw(self):
        """Gọi hàm stop_aw từ WlsCore"""
        if hasattr(self._wls, 'stop_aw') and not self.triggered:
            self._wls.stop_aw(0)  # Gọi với exit_code = 0
            self.triggered = True

    def effect_loop(self):
        """Vòng lặp chính của effect"""
        self.frame_count += 1

        # Tạo hiệu ứng màu đơn giản
        color_array = np.tile(self.color, (self.pixel_count, 1))

        # Thêm hiệu ứng nhấp nháy nhẹ
        brightness_factor = 0.5 + 0.5 * np.sin(self.frame_count * 0.1)
        color_array = color_array * brightness_factor

        self.pixels = color_array

        # Nếu chưa trigger và đã chạy được một thời gian, trigger stop_aw
        if not self.triggered and self.frame_count > 90:
            if self._config.get("auto_trigger", True):
                self._trigger_stop_aw()