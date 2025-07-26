import numpy as np
import voluptuous as vol
import math

from wls.color import parse_color, validate_color
from wls.effects.temporal import TemporalEffect


class BubbleEffect(TemporalEffect):

    NAME = "Bong bóng"
    CATEGORY = "1. Hiệu ứng cơ bản"
    
    def __init__(self, wls, config):
        super().__init__(wls, config)
        # Initialize state variables
        self.speed_counter = 0
        self.time_offset = 0
        self.pattern_size = 240  # Default pattern size
        # Initialize bubble pattern with default values
        self.bubble_pattern = np.zeros((3, self.pattern_size))

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "gradient_type",
                description="Loại gradient",
                default="rainbow",
            ): vol.In(["rainbow", "custom", "plasma", "aurora", "sunset"]),
            vol.Optional(
                "custom_colors",
                description="Màu tùy chỉnh (cho gradient custom)",
                default=["#FF0000", "#FFFF00", "#00FF00", "#00FFFF", "#0000FF", "#FF00FF"],
            ): vol.All([validate_color], vol.Length(min=2, max=20)),
            vol.Optional(
                "speed",
                description="Tốc độ bong bóng",
                default=1.0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=5.0)),
            vol.Optional(
                "reverse",
                description="Đảo chiều",
                default=False,
            ): bool,
            vol.Optional(
                "mirror",
                description="Phản chiếu",
                default=False,
            ): bool,
            vol.Optional(
                "bubble_size",
                description="Kích thước bong bóng",
                default=1.5,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=5.0)),
            vol.Optional(
                "bubble_count",
                description="Số lượng bong bóng",
                default=3,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
        }
    )

    def on_activate(self, pixel_count):
        self.speed_counter = 0
        self.time_offset = 0
        
        # Create extended pattern for smooth movement
        self.pattern_size = pixel_count * 4  # Larger pattern for smooth bubbles
        
        # Setup bubble pattern
        self._setup_bubble_pattern()

    def config_updated(self, config):
        # Only setup pattern if we have pixel count (after activation)
        if hasattr(self, 'pixel_count'):
            self.pattern_size = self.pixel_count * 4
            self._setup_bubble_pattern()

    def _setup_bubble_pattern(self):
        """Setup bubble pattern based on configuration"""
        if self._config["gradient_type"] == "rainbow":
            base_colors = self._create_rainbow_colors()
        elif self._config["gradient_type"] == "custom":
            base_colors = [parse_color(color) for color in self._config["custom_colors"]]
        elif self._config["gradient_type"] == "plasma":
            base_colors = [[255, 0, 255], [0, 255, 255], [255, 255, 0], [255, 0, 0]]
        elif self._config["gradient_type"] == "aurora":
            base_colors = [[0, 255, 100], [100, 255, 200], [0, 200, 255], [100, 100, 255]]
        elif self._config["gradient_type"] == "sunset":
            base_colors = [[255, 100, 0], [255, 200, 0], [255, 255, 100], [255, 150, 50]]
        
        self.bubble_pattern = self._create_bubble_pattern(base_colors)

    def _create_rainbow_colors(self):
        """Create rainbow color palette"""
        colors = []
        for i in range(6):
            hue = (i / 6) * 360
            # Convert HSV to RGB (simplified)
            c = 1.0
            x = c * (1 - abs((hue / 60) % 2 - 1))
            m = 0
            
            if 0 <= hue < 60:
                r, g, b = c, x, 0
            elif 60 <= hue < 120:
                r, g, b = x, c, 0
            elif 120 <= hue < 180:
                r, g, b = 0, c, x
            elif 180 <= hue < 240:
                r, g, b = 0, x, c
            elif 240 <= hue < 300:
                r, g, b = x, 0, c
            else:
                r, g, b = c, 0, x
                
            colors.append([int((r + m) * 255), int((g + m) * 255), int((b + m) * 255)])
        
        return colors

    def _create_bubble_pattern(self, base_colors):
        """Create bubble pattern with sine wave modulation"""
        pattern = np.zeros((3, self.pattern_size))
        
        bubble_count = self._config["bubble_count"]
        bubble_size = self._config["bubble_size"]
        
        for i in range(self.pattern_size):
            # Create multiple overlapping sine waves for bubble effect
            total_r, total_g, total_b = 0, 0, 0
            
            for bubble_idx in range(bubble_count):
                # Each bubble has different frequency and phase
                frequency = (bubble_idx + 1) * 0.02 / bubble_size
                phase = (bubble_idx * 2 * math.pi) / bubble_count
                
                # Calculate sine wave value
                wave_value = (math.sin(i * frequency + phase) + 1) / 2
                
                # Apply bubble envelope (Gaussian-like)
                envelope = math.exp(-((i % (self.pattern_size // bubble_count) - 
                                     (self.pattern_size // bubble_count) // 2) ** 2) / 
                                   (2 * (bubble_size * 10) ** 2))
                
                # Get color for this bubble
                color_idx = bubble_idx % len(base_colors)
                color = base_colors[color_idx]
                
                # Apply wave and envelope
                intensity = wave_value * envelope
                total_r += color[0] * intensity
                total_g += color[1] * intensity
                total_b += color[2] * intensity
            
            # Normalize and set pattern values
            pattern[0][i] = min(255, total_r)
            pattern[1][i] = min(255, total_g)
            pattern[2][i] = min(255, total_b)
        
        return pattern

    def effect_loop(self):
        """Main effect loop called by TemporalEffect"""
        # Calculate movement steps
        steps = self._get_roll_steps(self._config["speed"])
        
        # Update time offset for animation
        direction = -1 if self._config["reverse"] else 1
        self.time_offset = (self.time_offset + steps * direction) % self.pattern_size
        
        # Extract current window from pattern
        output_array = np.zeros((3, self.pixel_count))
        
        for i in range(self.pixel_count):
            pattern_idx = (self.time_offset + i) % self.pattern_size
            output_array[0][i] = self.bubble_pattern[0][pattern_idx]
            output_array[1][i] = self.bubble_pattern[1][pattern_idx]
            output_array[2][i] = self.bubble_pattern[2][pattern_idx]
        
        # Apply mirror effect if enabled
        if self._config["mirror"]:
            output_array = self._apply_mirror(output_array)
        
        # Set pixels
        self.pixels = output_array.T
        
        # Return speed modifier for TemporalEffect
        return 1.0

    def _apply_mirror(self, array):
        """Apply mirror effect"""
        mid = self.pixel_count // 2
        left_half = array[:, :mid]
        mirrored_array = array.copy()
        mirrored_array[:, mid:] = np.fliplr(left_half)
        return mirrored_array

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