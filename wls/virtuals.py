import itertools
import logging
import sys
import threading
import time
import timeit
from functools import cached_property

import numpy as np
import voluptuous as vol

from wls.color import parse_color
from wls.effects import DummyEffect
from wls.effects.math import interpolate_pixels
from wls.effects.melbank import (
    MAX_FREQ,
    MIN_FREQ,
    MIN_FREQ_DIFFERENCE,
    FrequencyRange,
)
from wls.events import (
    EffectClearedEvent,
    EffectSetEvent,
    Event,
    GlobalPauseEvent,
    VirtualConfigUpdateEvent,
    VirtualPauseEvent,
    VirtualUpdateEvent,
)

# from wls.config import save_config
from wls.transitions import Transitions
from wls.utils import fps_to_sleep_interval

_LOGGER = logging.getLogger(__name__)

color_list = ["red", "green", "blue", "cyan", "magenta", "#ffff00"]


class Virtual:

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "name", description="Tên đèn"
            ): str,
            vol.Required(
                "mapping",
                description="Span: Hiệu ứng kéo dài tất cả các phân đoạn. Đồng bộ: Hiệu ứng được đồng bộ trên mỗi phân đoạn",
                default="span",
            ): vol.In(["span", "copy"]),
            vol.Optional(
                "icon_name",
                description="Biểu tượng của đèn*",
                default="mdi:led-strip-variant",
            ): str,
            vol.Optional(
                "max_brightness",
                description="Độ sáng tối đa cho đèn",
                default=1.0,
            ): vol.All(vol.Coerce(float), vol.Range(min=0, max=1)),
            vol.Optional(
                "center_offset",
                description="Số lượng pixel từ trung tâm của đèn",
                default=0,
            ): int,
            vol.Optional(
                "preview_only",
                description="Xem trước các pixel mà không cần cập nhật đèn",
                default=False,
            ): bool,
            vol.Optional(
                "transition_time",
                description="Thời gian chuyển đổi giữa các hiệu ứng",
                default=0.4,
            ): vol.All(
                vol.Coerce(float),
                vol.Range(min=0, max=5, min_included=True, max_included=True),
            ),
            vol.Optional(
                "transition_mode",
                description="Kiểu chuyển đổi giữa các hiệu ứng",
                default="Thêm",
            ): vol.In([mode for mode in Transitions]),
            vol.Optional(
                "frequency_min",
                description="Tần số thấp nhất cho các hiệu ứng phản ứng âm thanh của đèn ảo này",
                default=MIN_FREQ,  # GET THIS FROM CORE AUDIO
            ): vol.All(
                vol.Coerce(int),
                vol.Range(
                    min=MIN_FREQ,
                    max=MAX_FREQ,
                ),
            ),  # AND HERE TOO,
            vol.Optional(
                "frequency_max",
                description="Tần số cao nhất cho các hiệu ứng nháy theo nhạc của đèn ảo này",
                default=MAX_FREQ,  # GET THIS FROM CORE AUDIO
            ): vol.All(
                vol.Coerce(int),
                vol.Range(
                    min=MIN_FREQ,
                    max=MAX_FREQ,
                ),
            ),  # AND HERE TOO,
        }
    )

    # vol.Required(
    #     "start_pixel",
    #     description="First pixel the virtual will map onto device (inclusive)",
    # ): int,
    # vol.Required(
    #     "end_pixel",
    #     description="Last pixel the virtual will map onto device (inclusive)",
    # ): int,
    # vol.Optional(
    #     "invert",
    #     description="Reverse the virtual mapping onto this device",
    #     default=False,
    # ): bool,

    _paused = False
    _active = False
    _output_thread = None
    _active_effect = None
    _transition_effect = None

    if (
        sys.version_info[0] == 3 and sys.version_info[1] >= 11
    ) or sys.version_info[0] >= 4:
        _min_time = time.get_clock_info("perf_counter").resolution
    else:
        _min_time = time.get_clock_info("monotonic").resolution

    def __init__(self, wls, config):
        def pause_effects(e):
            self.deactivate()

        def resume_effects(e):
            self.activate()

        self._wls = wls
        self._wls.events.add_listener(pause_effects, Event.GLOBAL_PAUSE)
        self._wls.events.add_listener(resume_effects, Event.GLOBAL_RESUME)
        self._config = config
        # the multiplier to fade in/out of an effect. -ve values mean fading
        # in, +ve mean fading out
        self.fade_timer = 0
        self._segments = []
        self._calibration = False
        self._highlight = -1
        self.lock = threading.Lock()

        self.frequency_range = FrequencyRange(
            self._config["frequency_min"], self._config["frequency_max"]
        )

        # list of devices in order of their mapping on the virtual
        # [[id, start, end, invert]...]
        # not a very good schema, but vol seems a bit handicapped in terms of lists.
        # this won't necessarily ensure perfectly validated segments, but it at
        # least gives an idea of the format
        self.SEGMENTS_SCHEMA = vol.Schema([self.validate_segment])

    def __del__(self):
        self.active = False

    def _valid_id(self, id):
        device = self._wls.devices.get(id)
        if device is not None:
            return id
        else:
            msg = f"Đèn {id} không hợp lệ"
            _LOGGER.warning(msg)
            raise ValueError(msg)

    def activate_segments(self, segments):
        for device_id, start_pixel, end_pixel, invert in segments:
            device = self._wls.devices.get(device_id)
            if not device.is_active():
                device.activate()
            device.add_segment(self.id, start_pixel, end_pixel, force=True)

    def deactivate_segments(self):
        for device in self._devices:
            device.clear_virtual_segments(self.id)

    def validate_segment(self, segment):
        valid = True
        msg = None

        if len(segment) != 4:
            msg = f"Định dạng phân đoạn {segment} không hợp lệ, phải là [device_id, start, end, invert]"
            valid = False

        device_id, start_pixel, end_pixel, invert = segment

        device = self._wls.devices.get(device_id)

        if device is None:
            msg = f"Đèn {device_id} không hợp lệ"
            valid = False
        else:
            max_pixel_count = device.pixel_count

            # Điều chỉnh start_pixel và end_pixel để đảm bảo chúng nằm trong phạm vi hợp lệ
            start_pixel = max(0, min(start_pixel, max_pixel_count - 1))
            end_pixel = max(0, min(end_pixel, max_pixel_count - 1))

            if start_pixel > end_pixel:
                msg = f"Pixel phân đoạn ({start_pixel} không hợp lệ, {end_pixel}). Đèn '{self.name}' có pixel hợp lệ giữa (0, {max_pixel_count - 1})"
                valid = False

        if not valid:
            _LOGGER.error(msg)
            raise ValueError(msg)
        else:
            return (device_id, start_pixel, end_pixel, invert)


    def invalidate_cached_props(self):
        # invalidate cached properties
        for prop in [
            "pixel_count",
            "refresh_rate",
            "_devices",
            "_segments_by_device",
        ]:
            if hasattr(self, prop):
                delattr(self, prop)

    def update_segments(self, segments_config):
        segments_config = [list(item) for item in segments_config]
        _segments = self.SEGMENTS_SCHEMA(segments_config)

        _pixel_count = self.pixel_count

        if _segments != self._segments:
            if self._active:
                self.deactivate_segments()
                # try to register this new set of segments
                # if it fails, restore previous segments and raise the error
                try:
                    self.activate_segments(_segments)
                except ValueError:
                    self.deactivate_segments()
                    self.activate_segments(self._segments)
                    raise

            self._segments = _segments

            self.invalidate_cached_props()

            _LOGGER.debug(
                f"Đèn ảo {self.id}: đã cập nhật với {len(self._segments)} phân đoạn, tộng cộng có {self.pixel_count} pixel"
            )

            # Restart active effect if total pixel count has changed
            # eg. devices might be reordered, but total pixel count is same
            # so no need to restart the effect
            if self.pixel_count != _pixel_count:
                # chenging segments is a deep edit, just flush any transition
                self.clear_transition_effect()
                self.transitions = Transitions(self.pixel_count)
                if self._active_effect is not None:
                    self._active_effect._deactivate()
                    if self.pixel_count > 0:
                        self._active_effect.activate(self)

            mode = self._config["transition_mode"]
            self.frame_transitions = self.transitions[mode]
        # Update internal config with new segment
        for idx, item in enumerate(self._wls.config["virtuals"]):
            if item["id"] == self.id:
                item["segments"] = self._segments
                self._wls.config["virtuals"][idx] = item
                break
        _LOGGER.debug(
            f"Virtual {self.id}: updated with {len(self._segments)} segments, totalling {self.pixel_count} pixels"
        )
        self._wls.virtuals.check_and_deactivate_devices()

    def set_preset(self, preset_info):
        category, effect_id, preset_id = preset_info

        # Create the effect and add it to the virtual
        try:
            effect_config = self._wls.config[category][effect_id][preset_id][
                "config"
            ]
        except KeyError:
            _LOGGER.error(f"Không thể tìm thấy cài trước: {preset_info}")
            return
        effect = self._wls.effects.create(
            wls=self._wls, type=effect_id, config=effect_config
        )
        self.set_effect(effect)

    def set_effect(self, effect):
        # Thêm timeout cho khóa để tránh deadlock
        lock_acquired = self.lock.acquire(timeout=3.0)  # Timeout 3 giây
        if not lock_acquired:
            error = f"Đèn ảo {self.id}: Không thể lấy khóa sau 3 giây, có thể có deadlock"
            _LOGGER.error(error)
            # Không raise exception ở đây để tránh crash ứng dụng
            return

        try:
            if not self._devices:
                error = f"Đèn ảo {self.id}: Không thể kích hoạt, không có phân đoạn thiết bị được định cấu hình"
                _LOGGER.warning(error)
                raise ValueError(error)

            if (
                self._config["transition_mode"] != "None"
                and self._config["transition_time"] > 0
            ):
                self.transition_frame_total = (
                    self.refresh_rate * self._config["transition_time"]
                )
                self.transition_frame_counter = 0
                self.clear_transition_effect()

                if self._active_effect is None:
                    self._transition_effect = DummyEffect(self.pixel_count)
                else:
                    self._transition_effect = self._active_effect
            else:
                # no transition effect to clean up, so clear the active effect now!
                self.clear_active_effect()

            self._active_effect = effect
            self._active_effect.activate(self)

            # Cập nhật device_states trong config
            if "device_states" not in self._wls.config:
                self._wls.config["device_states"] = {}

            if "device_effects" not in self._wls.config:
                self._wls.config["device_effects"] = {}

            # Nếu virtual này đại diện cho một thiết bị thực, cập nhật trạng thái và hiệu ứng của thiết bị đó
            if hasattr(self, 'is_device') and self.is_device is not None:
                device_id = str(self.is_device)
                self._wls.config["device_states"][device_id] = True
                self._wls.config["device_effects"][device_id] = effect.type
                _LOGGER.debug(f"Đã cập nhật trạng thái bật và hiệu ứng {effect.type} cho thiết bị {device_id}")

            self._wls.events.fire_event(
                EffectSetEvent(
                    self._active_effect.name,
                    self._active_effect.id,
                    self.active_effect.config,
                    self.id,
                )
            )
        except Exception as e:
            _LOGGER.error(f"Lỗi trong set_effect: {e}")
            raise
        finally:
            # Đảm bảo luôn giải phóng khóa
            self.lock.release()

        try:
            self.active = True
        except RuntimeError:
            self.active = False
            raise

    def transition_to_active(self):
        self._active_effect = self._transition_effect
        self._transition_effect = None

    def active_to_transition(self):
        self._transition_effect = self._active_effect
        self._active_effect = None

    def clear_effect(self):
        # Thêm timeout cho khóa để tránh deadlock
        lock_acquired = self.lock.acquire(timeout=3.0)  # Timeout 3 giây
        if not lock_acquired:
            error = f"Đèn ảo {self.id}: Không thể lấy khóa sau 3 giây khi clear_effect, có thể có deadlock"
            _LOGGER.error(error)
            # Không raise exception ở đây để tránh crash ứng dụng
            return

        try:
            # Cập nhật trạng thái device_states trong config cho thiết bị cụ thể
            if "device_states" not in self._wls.config:
                self._wls.config["device_states"] = {}

            # Nếu virtual này đại diện cho một thiết bị thực, cập nhật trạng thái của thiết bị đó
            if hasattr(self, 'is_device') and self.is_device is not None:
                device_id = str(self.is_device)
                self._wls.config["device_states"][device_id] = False
                _LOGGER.debug(f"Đã cập nhật trạng thái tắt cho thiết bị {device_id}")

            # Lưu cấu hình
            from wls.config import save_config
            save_config(self._wls.config, self._wls.config_dir)

            # Phát sự kiện EffectClearedEvent
            self._wls.events.fire_event(EffectClearedEvent())
            self.clear_transition_effect()

            if (
                self._config["transition_mode"] != "None"
                and self._config["transition_time"] > 0
            ):
                self._transition_effect = self._active_effect
                self._active_effect = DummyEffect(self.pixel_count)

                self.transition_frame_total = (
                    self.refresh_rate * self._config["transition_time"]
                )
                self.transition_frame_counter = 0
            else:
                # no transition effect to clean up, so clear the active effect now!
                self.clear_active_effect()

            self._wls.loop.call_later(
                self._config["transition_time"], self.clear_frame
            )
        except Exception as e:
            _LOGGER.error(f"Lỗi trong clear_effect: {e}")
        finally:
            # Đảm bảo luôn giải phóng khóa
            self.lock.release()

    def clear_transition_effect(self):
        if self._transition_effect is not None:
            self._transition_effect._deactivate()
        self._transition_effect = None

    def set_brightness(self, brightness_value):
        """
        Set brightness for this virtual device.

        Args:
            brightness_value (float): Brightness value between 0.0 and 1.0
        """
        # Ensure brightness is within valid range
        brightness_value = max(0.0, min(brightness_value, 1.0))

        # Update max_brightness in config
        self._config["max_brightness"] = brightness_value

        _LOGGER.debug(f"Đèn ảo {self.id}: Đã đặt độ sáng thành {int(brightness_value * 100)}%")

    def clear_active_effect(self):
        if self._active_effect is not None:
            self._active_effect._deactivate()
        self._active_effect = None

    def clear_frame(self):
        self.lock.acquire()
        self.clear_active_effect()
        self.clear_transition_effect()

        if self._active:
            # Clear all the pixel data before deactivating the device
            self.assembled_frame = np.zeros((self.pixel_count, 3))
            self.flush(self.assembled_frame)
            self._wls.events.fire_event(
                VirtualUpdateEvent(self.id, self.assembled_frame)
            )
            self.lock.release()
            self.deactivate()
        else:
            self.lock.release()

    def force_frame(self, color):
        """
        Force all pixels in device to color
        Use for pre-clearing in calibration scenarios
        """
        self.assembled_frame = np.full((self.pixel_count, 3), color)
        self.flush(self.assembled_frame)
        self._wls.events.fire_event(
            VirtualUpdateEvent(self.id, self.assembled_frame)
        )

    def set_calibration(self, calibration):
        self._calibration = calibration
        if calibration is False:
            self._highlight = -1

    def set_highlight(self, highlight):
        if self._calibration is False:
            return f"Cannot set highlight when {self.name} is not in calibration mode"
        if highlight < -1 or highlight > ( len(self._segments) - 1):
            return f"Highlight must be between -1 (off) and {len(self._segments) - 1} inclusive"
        self._highlight = highlight
        return None

    @property
    def active_effect(self):
        return self._active_effect

    def thread_function(self):
        while True:
            if not self._active:
                break
            start_time = timeit.default_timer()
            # we need to lock before we test, or we could deactivate
            # between test and execution
            self.lock.acquire()
            if (
                self._active_effect
                and self._active_effect.is_active
                and hasattr(self._active_effect, "pixels")
            ):
                # self.assembled_frame = await self._wls.loop.run_in_executor(
                #     self._wls.thread_executor, self.assemble_frame
                # )
                self.assembled_frame = self.assemble_frame()
                if self.assembled_frame is not None and not self._paused:
                    if not self._config["preview_only"]:
                        # self._wls.thread_executor.submit(self.flush)
                        # await self._wls.loop.run_in_executor(
                        #     self._wls.thread_executor, self.flush
                        # )
                        self.flush()

                    self._wls.events.fire_event(
                        VirtualUpdateEvent(self.id, self.assembled_frame)
                    )
            self.lock.release()

            # adjust for the frame assemble time, min allowed sleep 1 ms
            # this will be more frame accurate on high res sleep systems
            run_time = timeit.default_timer() - start_time
            sleep_time = max(
                0.001, fps_to_sleep_interval(self.refresh_rate) - run_time
            )
            time.sleep(sleep_time)

            # use an aggressive check for did we sleep against expected min clk
            # for all high res scenarios this will be passive
            # for unexpected high res sleep on windows scenarios it will adapt
            pass_time = timeit.default_timer() - start_time
            if pass_time < (self._min_time / 2):
                time.sleep(max(0.001, self._min_time - pass_time))

    def assemble_frame(self):
        """
        Assembles the frame to be flushed.
        """
        # Get and process active effect frame
        self._active_effect._render()
        frame = self._active_effect.get_pixels()
        if frame is None:
            return
        frame[frame > 255] = 255
        frame[frame < 0] = 0
        # np.clip(frame, 0, 255, frame)

        if self._config["center_offset"]:
            frame = np.roll(frame, self._config["center_offset"], axis=0)

        # This part handles blending two effects together
        if (
            self._transition_effect is not None
            and self._transition_effect.is_active
            and hasattr(self._transition_effect, "pixels")
        ):
            # Get and process transition effect frame
            self._transition_effect._render()
            transition_frame = self._transition_effect.get_pixels()
            transition_frame[transition_frame > 255] = 255
            transition_frame[transition_frame < 0] = 0

            if self._config["center_offset"]:
                transition_frame = np.roll(
                    transition_frame,
                    self._config["center_offset"],
                    axis=0,
                )

            # Blend both frames together
            self.transition_frame_counter += 1
            self.transition_frame_counter = min(
                max(self.transition_frame_counter, 0),
                self.transition_frame_total,
            )

            if self.transition_frame_total == 0:
                # the transition should happen immediately
                weight = 1
            else:
                # calculates how far in we are in the transition
                # 0 = previous effect and 1 = next effect
                weight = (
                        self.transition_frame_counter
                        / self.transition_frame_total
                    )

            # we will pre validate the transition, which will generate a sentry report if it fails and return False
            if self.transitions.pre_validate(frame, transition_frame):
                # only call the transition effect if it will not crash
                self.frame_transitions(
                    self.transitions, frame, transition_frame, weight
                )
            if self.transition_frame_counter == self.transition_frame_total:
                self.clear_transition_effect()

        # Áp dụng độ sáng của thiết bị ảo
        np.multiply(frame, self._config["max_brightness"], frame)

        return frame

    def activate(self):
        if not self._devices:
            error = f"Đèn ảo {self.id}: Không thể kích hoạt, không có phân đoạn thiết bị được định cấu hình"
            _LOGGER.warning(error)
            raise RuntimeError(error)
        if not self._active_effect:
            error = f"Đèn ảo {self.id}: Không thể kích hoạt, không có hiệu ứng được định cấu hình"
            _LOGGER.warning(error)
            raise RuntimeError(error)

        if hasattr(self, "_thread"):
            self._thread.join()

        _LOGGER.debug(
            f"Đèn ảo {self.id}: Kích hoạt với các phân đoạn {self._segments}"
        )
        if not self._active:
            try:
                self.activate_segments(self._segments)
            except ValueError as e:
                _LOGGER.error(e)
            self._active = True

        # self.thread_function()

        self._thread = threading.Thread(
            name=f"Virtual: {self.id}", target=self.thread_function
        )
        self._thread.start()
        self._wls.events.fire_event(VirtualPauseEvent(self.id))
        # self._task = self._wls.loop.create_task(self.thread_function())
        # self._task.add_done_callback(lambda task: task.result())

    def deactivate(self):
        self._active = False
        if (threading.current_thread() != self._thread):
            self._thread.join()
        self.deactivate_segments()
        self._wls.events.fire_event(VirtualPauseEvent(self.id))
        self._wls.virtuals.check_and_deactivate_devices()

    # @lru_cache(maxsize=32)
    # def _normalized_linspace(self, size):
    #     return np.linspace(0, 1, size)

    # def interp_channel(self, channel, x_new, x_old):
    #     return np.interp(x_new, x_old, channel)

    # # TODO cache this!
    # # need to be able to access pixels but not through args
    # # @lru_cache(maxsize=8)
    # def interpolate(self, pixels, new_length):
    #     """Resizes the array by linearly interpolating the values"""
    #     if len(pixels) == new_length:
    #         return pixels

    #     x_old = self._normalized_linspace(len(pixels))
    #     x_new = self._normalized_linspace(new_length)

    #     z = np.apply_along_axis(self.interp_channel, 0, pixels, x_new, x_old)
    #     return z

    def flush(self, pixels=None):
        """
        Flushes the provided data to the devices.
        """
        # _LOGGER.info(f"Virtual {self.id}: Flushing frame")

        if pixels is None:
            pixels = self.assembled_frame

        color_cycle = itertools.cycle(color_list)

        for device_id, segments in self._segments_by_device.items():
            data = []
            device = self._wls.devices.get(device_id)

            if self._calibration:
                # set data to black for full length of led strip allow other segments to overwrite
                data.append(
                    (
                        np.array([0.0, 0.0, 0.0], dtype=float),
                        0,
                        device.pixel_count - 1,
                    )
                )

            for index, (start, stop, step, device_start, device_end) in enumerate(segments):
                if self._calibration:
                    color = np.array(parse_color(next(color_cycle)), dtype=float)
                    if self._highlight == index:
                        color = np.array(parse_color("white"), dtype=float)

                    data.append((color, device_start, device_end))
                else:
                    if self._config["mapping"] == "span":
                        data.append(
                            (pixels[start:stop:step], device_start, device_end)
                        )
                    elif self._config["mapping"] == "copy":
                        target_len = device_end - device_start + 1
                        data.append(
                            (
                                interpolate_pixels(pixels, target_len)[::step],
                                device_start,
                                device_end,
                            )
                        )

            if device is None:
                _LOGGER.warning(
                    f"Đèn {self.id} đã được xoá,  hiện không có thiết bị nào đang hoạt động."
                )
                self.deactivate()
            elif device.is_active():
                device.update_pixels(self.id, data)
        # self.interpolate.cache_clear()

    @property
    def name(self):
        return self._config["name"]

    @property
    def max_brightness(self):
        return self._config["max_brightness"] * 256

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, active):
        active = bool(active)
        if active and not self._active:
            self.activate()
        if not active and self._active:
            self.deactivate()
        self._active = active

    @property
    def id(self) -> str:
        """Returns the id for the virtual"""
        return getattr(self, "_id", None)

    @property
    def segments(self):
        return self._segments

    @cached_property
    def _segments_by_device(self):
        """
        List to help split effect output to the correct pixels of each device
        """
        data_start = 0
        segments_by_device = {}
        for device_id, device_start, device_end, inverse in self._segments:
            segment_width = device_end - device_start + 1
            if not inverse:
                start = data_start
                stop = data_start + segment_width
                step = 1
            else:
                start = data_start + segment_width - 1
                stop = None if data_start == 0 else data_start - 1
                step = -1
            segment_info = (
                start,
                stop,
                step,
                device_start,
                device_end,
            )
            if device_id in segments_by_device.keys():
                segments_by_device[device_id].append(segment_info)
            else:
                segments_by_device[device_id] = [segment_info]
            data_start += segment_width
        return segments_by_device

    @cached_property
    def _devices(self):
        """
        Return an iterable of the device object of each segment of the virtual
        """
        return list(
            self._wls.devices.get(device_id)
            for device_id in {segment[0] for segment in self._segments}
        )

    @cached_property
    def refresh_rate(self):
        if not self._devices:
            return False
        return min(device.max_refresh_rate for device in self._devices)

    @cached_property
    def pixel_count(self):
        if self._config["mapping"] == "span":
            total = 0
            for device_id, start_pixel, end_pixel, invert in self._segments:
                total += end_pixel - start_pixel + 1
            return total
        elif self._config["mapping"] == "copy":
            if self._segments:
                return max(
                    end_pixel - start_pixel + 1
                    for _, start_pixel, end_pixel, _ in self._segments
                )
            else:
                return 0

    @staticmethod
    def schema() -> vol.Schema:
        """returns the schema for the object"""
        return Virtual.CONFIG_SCHEMA

    @property
    def config(self) -> dict:
        """Returns the config for the object"""
        return getattr(self, "_config", None)

    def update_config(self, config):
        self.config = config

    @config.setter
    def config(self, new_config):
        """Updates the config for an object"""
        if self._config is not None:
            _config = {**self._config, **new_config}
        else:
            _config = new_config

        _config = self.CONFIG_SCHEMA(_config)

        if hasattr(self, "_config"):
            if _config["mapping"] != self._config["mapping"]:
                self.invalidate_cached_props()
            if (
                _config["transition_mode"] != self._config["transition_mode"]
                or _config["transition_time"]
                != self._config["transition_time"]
            ):
                self.frame_transitions = self.transitions[
                    _config["transition_mode"]
                ]
                if self._wls.config["global_transitions"]:
                    for virtual_id in self._wls.virtuals:
                        if virtual_id == self.id:
                            continue
                        virtual = self._wls.virtuals.get(virtual_id)
                        virtual.frame_transitions = virtual.transitions[
                            _config["transition_mode"]
                        ]
                        virtual._config["transition_time"] = _config[
                            "transition_time"
                        ]
                        virtual._config["transition_mode"] = _config[
                            "transition_mode"
                        ]

            if (
                "frequency_min" in _config.keys()
                or "frequency_max" in _config.keys()
            ):
                # if these are in config, manually sanitise them
                _config["frequency_min"] = min(
                    _config["frequency_min"], MAX_FREQ - MIN_FREQ_DIFFERENCE
                )
                _config["frequency_min"] = max(
                    _config["frequency_min"], MIN_FREQ
                )
                _config["frequency_max"] = max(
                    _config["frequency_max"], MIN_FREQ + MIN_FREQ_DIFFERENCE
                )
                _config["frequency_max"] = min(
                    _config["frequency_max"], MAX_FREQ
                )
                diff = abs(_config["frequency_max"] - _config["frequency_min"])
                if diff < MIN_FREQ_DIFFERENCE:
                    _config["frequency_max"] += diff
                # if they're changed, clear some cached properties
                # so the changes take effect
                if (
                    (
                        _config["frequency_min"]
                        != self._config["frequency_min"]
                        or _config["frequency_max"]
                        != self._config["frequency_max"]
                    )
                    and (self._active_effect is not None)
                    and (
                        hasattr(
                            self._active_effect, "clear_melbank_freq_props"
                        )
                    )
                ):
                    self._active_effect.clear_melbank_freq_props()

        setattr(self, "_config", _config)

        self.frequency_range = FrequencyRange(
            self._config["frequency_min"], self._config["frequency_max"]
        )

        self._wls.events.fire_event(
            VirtualConfigUpdateEvent(self.id, self._config)
        )


class Virtuals:
    """Thin wrapper around the device registry that manages virtuals"""

    PACKAGE_NAME = "wls.virtuals"
    _paused = False

    def __init__(self, wls):
        # super().__init__(wls, Virtual, self.PACKAGE_NAME)

        def cleanup_effects(e):
            self.clear_all_effects()

        self._wls = wls
        self._wls.events.add_listener(cleanup_effects, Event.WLS_SHUTDOWN)
        self._virtuals = {}

    def create_from_config(self, config, pause_all=False):
        for virtual in config:
            _LOGGER.debug(f"Đang tải ảo từ cấu hình: {virtual}")
            self._wls.virtuals.create(
                id=virtual["id"],
                config=virtual["config"],
                is_device=virtual["is_device"],
                wls=self._wls,
            )
            if "segments" in virtual:
                try:
                    self._wls.virtuals.get(virtual["id"]).update_segments(
                        virtual["segments"]
                    )
                except vol.MultipleInvalid:
                    _LOGGER.warning(
                        "Virtual Segment Changed. Not restoring segment"
                    )
                    continue
                except RuntimeError:
                    pass

            if "effect" in virtual:
                try:
                    effect = self._wls.effects.create(
                        wls=self._wls,
                        type=virtual["effect"]["type"],
                        config=virtual["effect"]["config"],
                    )
                    self._wls.virtuals.get(virtual["id"]).set_effect(effect)
                except vol.MultipleInvalid:
                    _LOGGER.warning(
                        "Lược đồ hiệu ứng đã thay đổi. Không khôi phục hiệu ứng"
                    )
                except RuntimeError:
                    pass

            # This adds support for configs that are configured as paused
            # via the active key if it exists. Let the setter deal with it
            if "active" in virtual and not virtual["active"]:
                self._wls.virtuals.get(virtual["id"]).active = False

            # global pause is handled differently to virtual pause
            if pause_all:
                self._wls.virtuals.get(virtual["id"])._paused = True

            self._wls.events.fire_event(
                VirtualConfigUpdateEvent(virtual["id"], virtual["config"])
            )

    def schema(self):
        return Virtual.CONFIG_SCHEMA

    def create(self, id=None, *args, **kwargs):
        """Creates a virtual"""

        # Find the first valid id based on what is already in the registry
        dupe_id = id
        dupe_index = 1
        while id in self._virtuals.keys():
            id = f"{dupe_id}-{dupe_index}"
            dupe_index = dupe_index + 1

        # Create the new virtual and validate the schema.
        _config = kwargs.pop("config", None)
        _is_device = kwargs.pop("is_device", False)
        if _config is not None:
            _config = Virtual.CONFIG_SCHEMA(_config)
            obj = Virtual(config=_config, *args, **kwargs)
        else:
            obj = Virtual(*args, **kwargs)

        # Attach some common properties
        setattr(obj, "_id", id)
        setattr(obj, "is_device", _is_device)

        # Store the object into the internal list and return it
        self._virtuals[id] = obj
        return obj

    def destroy(self, id):
        if id not in self._virtuals:
            raise AttributeError(
                ("Đối tượng có id '{}' không tồn tại.").format(id)
            )
        del self._virtuals[id]

    def __iter__(self):
        return iter(self._virtuals)

    def values(self):
        return self._virtuals.values()

    def clear_all_effects(self):
        for virtual in self.values():
            virtual.clear_frame()

    def pause_all(self):
        self._paused = not self._paused
        for virtual in self.values():
            virtual._paused = self._paused
        self._wls.events.fire_event(GlobalPauseEvent())

    def get(self, *args):
        return self._virtuals.get(*args)

    def check_and_deactivate_devices(self):
        """
        Checks all active virtuals and segments to compile a list of active devices,
        then deactivates any active devices not in that list.
        This process ensures that devices are only deactivated if no virtual or segment
        is using them, which is especially relevant during virtual or segment deactivation
        or reconfiguration.
        Note: This is a relatively expensive operation but only runs when a virtual
        is deactivated or segments are modified.
        """

        active_devices = set()
        for virtual in self.values():
            if virtual.active:
                for device_id, _, _, _ in virtual.segments:
                    active_devices.add(device_id)
        for device in self._wls.devices.values():
            if device.id not in active_devices and device.is_active():
                _LOGGER.info(
                    f"Deactivating device {device.id} as it is not in use by any active virtuals"
                )
                device.deactivate()

def update_effect_config(config, virtual_id, effect):
    """
    Update the configuration of a virtual effect.
    This function is important for maintaining both the active effect and adding
    to the collection of effects configs on the virtual
    Args:
        config (dict): The current config structure
        virtual_id (str): The ID of the virtual effect.
        effect (Effect): The effect object containing the updated configuration.
    Returns:
        None
    """
    # Store as both the active effect to protect existing code, and one of effects
    virtual = next(
        (item for item in config["virtuals"] if item["id"] == virtual_id),
        None,
    )
    if virtual:
        if not ("effects" in virtual):
            virtual["effects"] = {}
        virtual["effects"][effect.type] = {}
        virtual["effects"][effect.type]["type"] = effect.type
        virtual["effects"][effect.type]["config"] = effect.config
        if not ("effect" in virtual):
            virtual["effect"] = {}
        virtual["effect"]["type"] = effect.type
        virtual["effect"]["config"] = effect.config