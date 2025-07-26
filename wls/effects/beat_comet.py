import numpy as np
import voluptuous as vol

from wls.effects.audio import AudioReactiveEffect
from wls.effects.gradient import GradientEffect


class BeatCometAudioEffect(AudioReactiveEffect, GradientEffect):

    NAME = "Sao chổi"
    CATEGORY = "2. Hiệu ứng nháy theo nhạc"

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Optional(
                "speed",
                description="Tốc độ trượt",
                default=0.5,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=2.0)),
            vol.Optional(
                "bar_length",
                description="Độ dài thanh",
                default=15,
            ): vol.All(vol.Coerce(int), vol.Range(min=3, max=50)),
            vol.Optional(
                "cometr_length",
                description="Độ dài trượt khi có beat",
                default=25,
            ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
            vol.Optional(
                "decay",
                description="Độ mờ dần",
                default=0.5,
            ): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=0.99)),
            vol.Optional(
                "random_color",
                description="Màu ngẫu nhiên cho mỗi thanh",
                default=True,
            ): bool,
            vol.Optional(
                "comet_intensity",
                description="Độ chói của đầu sao chổi",
                default=10,
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=10.0)),
            vol.Optional(
                "spark_effect",
                description="Hiệu ứng tia lửa khi trượt",
                default=True,
            ): bool,
            vol.Optional(
                "gradient_roll",
                description="Tốc độ dải mầu",
                default=1,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=10)),
        }
    )

    def on_activate(self, pixel_count):
        self.current_position = 0.0  # Use float for smooth movement
        self.prev_output = np.zeros((3, pixel_count))
        self.speed_counter = 0
        self.beat_detected = False

        # Beat detection variables
        self.beat_history = []
        self.last_beat_time = 0

        # Smooth sliding variables
        self.target_position = 0.0  # Target position for smooth sliding
        self.comet_speed = 0.0  # Current sliding speed
        self.is_sliding = False  # Whether currently in beat comet mode

        # Comet effect variables
        self.current_speed = 0.0  # Current movement speed for dynamic tail
        self.spark_particles = []  # List of spark particles [(pos, brightness, age)]

        # Initialize pixels array first (needed for gradient system)
        self.pixels = np.zeros((pixel_count, 3))

        # Current bar color (will be updated when beat detected or random_color = True)
        self.current_bar_color = self._get_bar_color()

    def audio_data_updated(self, data):
        # Use WLS2's built-in beat detection
        self.beat_detected = data.volume_beat_now()

        # Handle beat detection for smooth sliding
        if self.beat_detected:
            # Update bar color for random_color mode
            if self._config["random_color"]:
                self.current_bar_color = self._get_bar_color()

            # Start smooth comet to new target position
            comet_distance = self._config["cometr_length"]
            self.target_position = (self.current_position + comet_distance) % self.pixel_count

            # Set sliding speed (complete comet in ~10 frames for smoothness)
            self.comet_speed = comet_distance / 10.0
            self.is_sliding = True

    def _get_bar_color(self):
        """Get color for the sliding bar from gradient"""
        if self._config["random_color"]:
            # Random position in gradient for variety
            gradient_position = np.random.uniform(0.0, 1.0)
        else:
            # Fixed position in gradient (center)
            # Gradient roll will automatically change colors over time
            gradient_position = 0.5

        return self.get_gradient_color(gradient_position)

    def _draw_comet(self, output, head_position, base_length, color):
        """Draw a comet-like shape with bright head, fading tail and spark effects"""
        head_pos = int(head_position) % self.pixel_count

        # Add spark effects FIRST (so they appear behind comet body)
        if self._config["spark_effect"] and self.current_speed > 0.1:
            self._add_spark_effects(output, head_position, color)

        # Calculate dynamic tail length with controlled growth
        # Limit speed factor to prevent excessive length during beat comets
        speed_factor = max(1.0, min(2.5, self.current_speed * 1.5))  # Cap speed factor at 2.5x
        dynamic_length = int(base_length * speed_factor)

        # More conservative length cap to preserve spark visibility
        max_length = min(self.pixel_count // 3, base_length * 2)  # Max 1/3 strip or 2x base
        dynamic_length = min(dynamic_length, max_length)

        # Draw main comet body
        for i in range(dynamic_length):
            pos = (head_pos - i) % self.pixel_count

            # Calculate position ratio for color and brightness
            ratio = i / dynamic_length

            # Brightness falloff with enhanced head intensity
            if i == 0:  # Head
                brightness = self._config["comet_intensity"]  # Extra bright head
            else:
                brightness = max(0.0, 1.0 - ratio)
                brightness = brightness ** 0.3  # Softer falloff curve

            # Color gradient from head to tail
            head_color = color
            tail_color = color * 0.3  # Darker tail color
            gradient_color = head_color * (1 - ratio) + tail_color * ratio

            # Apply brightness to gradient color
            comet_color = gradient_color * brightness

            # Blend with existing output (additive)
            output[0][pos] = min(255, output[0][pos] + comet_color[0])
            output[1][pos] = min(255, output[1][pos] + comet_color[1])
            output[2][pos] = min(255, output[2][pos] + comet_color[2])

    def _add_spark_effects(self, output, head_position, color):
        """Add spark/smoke effects behind the comet"""
        # Generate new spark particles based on speed
        spark_probability = min(0.9, self.current_speed * 0.8)  # Higher speed = more sparks
        if np.random.random() < spark_probability:
            # Create spark further behind head to avoid comet body overlap
            base_distance = self._config["bar_length"] + 3  # Start after comet tail
            extra_distance = np.random.randint(2, 8)  # Additional random distance
            spark_distance = base_distance + extra_distance
            spark_pos = (head_position - spark_distance) % self.pixel_count

            # Add spark particle: [position, brightness, age]
            spark_brightness = np.random.uniform(0.4, 0.9)  # Brighter sparks
            self.spark_particles.append([spark_pos, spark_brightness, 0])

        # Update and draw existing spark particles
        active_sparks = []
        for spark in self.spark_particles:
            pos, brightness, age = spark

            # Age the spark
            age += 1
            brightness *= 0.85  # Fade over time

            # Keep spark if still visible
            if brightness > 0.08 and age < 20:  # Longer lasting, brighter threshold
                # Draw spark with enhanced visibility
                spark_color = color * brightness * 0.8  # Brighter than before

                # Add slight orange/yellow tint to sparks for distinction
                spark_color[0] = min(255, spark_color[0] * 1.1)  # More red
                spark_color[1] = min(255, spark_color[1] * 1.05)  # Slightly more green
                spark_color[2] = min(255, spark_color[2] * 0.9)   # Less blue

                pos_int = int(pos) % self.pixel_count
                output[0][pos_int] = min(255, output[0][pos_int] + spark_color[0])
                output[1][pos_int] = min(255, output[1][pos_int] + spark_color[1])
                output[2][pos_int] = min(255, output[2][pos_int] + spark_color[2])

                # Update spark data
                spark[1] = brightness
                spark[2] = age
                active_sparks.append(spark)

        # Keep only active sparks
        self.spark_particles = active_sparks

    def render(self):
        # Apply decay to previous output
        output = (self.prev_output * self._config["decay"]).astype(np.float32)

        # Handle smooth sliding movement
        if self.is_sliding:
            # Move towards target position
            distance_to_target = self.target_position - self.current_position

            # Handle wrap-around for circular movement
            if abs(distance_to_target) > self.pixel_count / 2:
                if distance_to_target > 0:
                    distance_to_target -= self.pixel_count
                else:
                    distance_to_target += self.pixel_count

            # Move towards target
            if abs(distance_to_target) <= self.comet_speed:
                # Reached target
                self.current_position = self.target_position
                self.is_sliding = False
                self.current_speed = 0.0  # Reset speed when sliding stops
                self.comet_speed = 0.0
            else:
                # Continue sliding
                if distance_to_target > 0:
                    self.current_position += self.comet_speed
                else:
                    self.current_position -= self.comet_speed

                # Keep position in bounds
                self.current_position = self.current_position % self.pixel_count

                # Track current speed for comet effects (sliding is fast)
                self.current_speed = self.comet_speed
        else:
            # Normal movement when not sliding
            steps = self._get_roll_steps(self._config["speed"])
            self.current_position = (self.current_position + steps) % self.pixel_count

            # Track current speed for comet effects (normal movement is slower)
            self.current_speed = steps * 0.5

        # Update bar color for non-random mode (gradient roll effect)
        if not self._config["random_color"]:
            self.current_bar_color = self._get_bar_color()

        # Draw the comet-shaped cometr
        comet_length = self._config["bar_length"]
        self._draw_comet(output, self.current_position, comet_length, self.current_bar_color)

        # Store for next frame
        self.prev_output = output.copy()

        # Set pixels
        self.pixels = output.T

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