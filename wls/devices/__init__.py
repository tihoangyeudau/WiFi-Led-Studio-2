import asyncio
import logging
import socket
import time
import sys
from abc import abstractmethod
from functools import cached_property, partial

import numpy as np
import serial
import serial.tools.list_ports
import voluptuous as vol
import zeroconf
import math  # Importing the math module

from wls.config import save_config
from wls.events import DeviceCreatedEvent, DeviceUpdateEvent, Event
from wls.utils import (
    AVAILABLE_FPS,
    RML,
    BaseRegistry,
    RegistryLoader,
    async_fire_and_forget,
    generate_id,
    resolve_destination,
    rml_support_DDP,
)

_LOGGER = logging.getLogger(__name__)


def fps_validator(value):
    if not isinstance(value, int):
        raise ValueError("fps phải là một số nguyên")
    return next(
        (f for f in AVAILABLE_FPS.keys() if f >= value),
        list(AVAILABLE_FPS.keys())[-1],
    )


@BaseRegistry.no_registration
class Device(BaseRegistry):
    @staticmethod
    @property
    def CONFIG_SCHEMA():
        return vol.Schema(
            {
                vol.Optional(
                    "icon_name",
                    description="https://material-ui.com/components/material-icons/",
                    default="mdi:led-strip",
                ): str,
                vol.Optional(
                    "center_offset",
                    description="Số lượng LED bù vào trung tâm của đèn",
                    default=0,
                ): int,
                vol.Optional(
                    "refresh_rate",
                    description="Target rate that pixels are sent to the device",
                    default=next(
                        (f for f in AVAILABLE_FPS if f >= 60),
                        list(AVAILABLE_FPS)[-1],
                    ),
                ): fps_validator,
            }
        )

    _active = False

    def __init__(self, wls, config):
        self._wls = wls
        self._config = config
        self._segments = []
        self._pixels = None
        self._silence_start = None
        self._device_type = ""
        self._online = True

    def __del__(self):
        if self._active:
            self.deactivate()

    def update_config(self, config):
        # TODO: Sync locks to ensure everything is thread safe
        if self._config is not None:
            config = {**self._config, **config}

        validated_config = type(self).schema()(config)
        self._config = validated_config

        # Iterate all the base classes and check to see if there is a custom
        # implementation of config updates. If to notify the base class.
        valid_classes = list(type(self).__bases__)
        valid_classes.append(type(self))
        for base in valid_classes:
            if hasattr(base, "config_updated"):
                if base.config_updated != super(base, base).config_updated:
                    base.config_updated(self, validated_config)

        _LOGGER.info(
            f"Đèn {self.name} đã cập nhật cấu hình {validated_config}."
        )

        for virtual_id in self._wls.virtuals:
            virtual = self._wls.virtuals.get(virtual_id)
            if virtual.is_device == self.id:
                segments = [[self.id, 0, self.pixel_count - 1, False]]
                virtual.update_segments(segments)
                virtual.invalidate_cached_props()

        for virtual in self._virtuals_objs:
            virtual.deactivate_segments()
            virtual.activate_segments(virtual._segments)

    def config_updated(self, config):
        """
        to be reimplemented by child classes
        """
        pass

    @property
    def pixel_count(self):
        return int(self._config["pixel_count"])

    def is_active(self):
        return self._active

    def is_online(self):
        return self._online

    def update_pixels(self, virtual_id, data):
        # update each segment from this virtual
        if not self._active:
            _LOGGER.warning(
                f"Cannot update pixels of inactive device {self.name}"
            )
            return

        for pixels, start, end in data:
            # protect against an empty race condition
            if pixels.shape[0] != 0:
                if np.shape(pixels) == (3,) or np.shape(
                    self._pixels[start : end + 1]
                ) == np.shape(pixels):
                    self._pixels[start : end + 1] = pixels

        if self.priority_virtual:
            if virtual_id == self.priority_virtual.id:
                frame = self.assemble_frame()
                self.flush(frame)
                # _LOGGER.debug(f"Device {self.id} flushed by Virtual {virtual_id}")

                self._wls.events.fire_event(
                    DeviceUpdateEvent(self.id, frame)
                )
        else:
            _LOGGER.warning(
                f"Flush skipped as {self.id} has no priority_virtual"
            )

    def assemble_frame(self):
        """
        Assembles the frame to be flushed. Currently this will just return
        the active channels pixels, but will eventually handle things like
        merging multiple segments segments and alpha blending channels
        """
        frame = self._pixels

        if self._config["center_offset"]:
            frame = np.roll(frame, self._config["center_offset"], axis=0)
        return frame

    def activate(self):
        self._pixels = np.zeros((self.pixel_count, 3))
        self._active = True

    def deactivate(self):
        self._pixels = None
        self._active = False
        # self.flush(np.zeros((self.pixel_count, 3)))

    @abstractmethod
    def flush(self, data):
        """
        Flushes the provided data to the device. This abstract method must be
        overwritten by the device implementation.
        """

    @property
    def name(self):
        return self._config["name"]

    @property
    def max_refresh_rate(self):
        return self._config["refresh_rate"]

    @property
    def refresh_rate(self):
        return self.priority_virtual.refresh_rate

    @cached_property
    def priority_virtual(self):
        """
        Returns the first virtual that has the highest refresh rate of all virtuals
        associated with this device
        """
        if not any(virtual.active for virtual in self._virtuals_objs):
            return None

        refresh_rate = max(
            virtual.refresh_rate
            for virtual in self._virtuals_objs
            if virtual.active
        )
        return next(
            virtual
            for virtual in self._virtuals_objs
            if virtual.refresh_rate == refresh_rate
        )

    @cached_property
    def _virtuals_objs(self):
        return list(
            self._wls.virtuals.get(virtual_id)
            for virtual_id in self.virtuals
        )

    @property
    def active_virtuals(self):
        """
        list of id of the virtuals active on this device.
        it's a list bc there can be more than one virtual streaming
        to a device.
        """
        return list(
            virtual.id for virtual in self._virtuals_objs if virtual.active
        )

    @property
    def online(self):
        """
        list of id of the virtuals active on this device.
        it's a list bc there can be more than one virtual streaming
        to a device.
        """
        return self._online

    @cached_property
    def virtuals(self):
        return list(segment[0] for segment in self._segments)

    def add_segment(self, virtual_id, start_pixel, end_pixel, force=False):
        # make sure this segment doesn't overlap with any others
        for _virtual_id, segment_start, segment_end in self._segments:
            if virtual_id == _virtual_id:
                continue
            overlap = (
                min(segment_end, end_pixel)
                - max(segment_start, start_pixel)
                + 1
            )
            if overlap > 0:
                virtual_name = self._wls.virtuals.get(virtual_id).name
                blocking_virtual = self._wls.virtuals.get(_virtual_id)
                if force:
                    blocking_virtual.deactivate()
                else:
                    msg = f"Không thể kích hoạt hiệu ứng! '{virtual_name}' chồng chéo với đèn ảo đang hoạt động '{blocking_virtual.name}'"
                    _LOGGER.warning(msg)
                    raise ValueError(msg)

        # if the segment is from a new device, we need to recheck our priority virtual
        if virtual_id not in (segment[0] for segment in self._segments):
            self.invalidate_cached_props()
        self._segments.append((virtual_id, start_pixel, end_pixel))
        _LOGGER.debug(
            f"Đèn {self.id}: Đã thêm phân đoạn {virtual_id, start_pixel, end_pixel}"
        )
        # We have added a segment, therefore the priority virtual may of changed
        self.invalidate_cached_props()

    def clear_virtual_segments(self, virtual_id):
        self._segments = [
            segment for segment in self._segments if segment[0] != virtual_id
        ]
        if self.priority_virtual:
            if virtual_id == self.priority_virtual.id:
                self.invalidate_cached_props()

    def clear_segments(self):
        self._segments = []

    def invalidate_cached_props(self):
        # invalidate cached properties
        for prop in ["priority_virtual", "_virtuals_objs", "virtuals"]:
            if hasattr(self, prop):
                delattr(self, prop)

    def remove_from_virtuals(self):
        # delete segments for this device in any virtuals

        for virtual in self._wls.virtuals.values():
            if not any(segment[0] == self.id for segment in virtual._segments):
                continue

            active = virtual.active
            if active:
                virtual.deactivate()
            virtual._segments = list(
                segment
                for segment in virtual._segments
                if segment[0] != self.id
            )

            # Update wls's config
            for idx, item in enumerate(self._wls.config["virtuals"]):
                if item["id"] == virtual.id:
                    item["segments"] = virtual.segments
                    self._wls.config["virtuals"][idx] = item
                    break

            if active:
                virtual.activate()


@BaseRegistry.no_registration
class NetworkedDevice(Device):
    """
    Networked device, handles resolving IP
    """

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "ip_address",
                description="Tên máy chủ hoặc địa chỉ IP của đèn",
            ): str,
        }
    )

    async def async_initialize(self):
        self._destination = None
        await self.resolve_address()

    async def resolve_address(self, success_callback=None):
        try:
            self._destination = await resolve_destination(
                self._wls.loop,
                self._wls.thread_executor,
                self._config["ip_address"],
            )
            _LOGGER.info(
                f"Đèn {self.name}: Đã giải quyết đích đến {self._destination}"
            )
            self._online = True
            if success_callback:
                success_callback()
        except ValueError as msg:
            self._online = False
            _LOGGER.warning(f"Device {self.name}: {msg}")

    def activate(self, *args, **kwargs):
        if self._destination is None:
            msg = f"Đèn {self.name}: Không thể kích hoạt, nó có trực tuyến không?"
            _LOGGER.warning(msg)
            callback = partial(self.activate, *args, **kwargs)
            async_fire_and_forget(
                self.resolve_address(success_callback=callback),
                loop=self._wls.loop,
            )
        else:
            self._online = True
            super().activate(*args, **kwargs)

    @property
    def destination(self):
        if self._destination is None:
            _LOGGER.warning(
                f"Đèn {self.name}: Đang tìm kiếm đèn ... Có trực tuyến không?"
            )
            async_fire_and_forget(
                self.resolve_address(), loop=self._wls.loop
            )
            return
        else:
            return self._destination


@BaseRegistry.no_registration
class UDPDevice(NetworkedDevice):

    def activate(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _LOGGER.debug(
            f"{self._device_type} đã bắt đầu gửi cho {self._config['name']}."
        )
        super().activate()

    def deactivate(self):
        super().deactivate()
        _LOGGER.debug(
            f"{self._device_type} đã dừng gửi cho {self._config['name']}."
        )
        self._sock = None

if sys.platform == 'win32':
    manufacturers = ['wch.cn', 'FTDI', 'Microsoft', 'Silicon Labs']

    class AvailableCOMPorts:
        ports = serial.tools.list_ports.comports()
        available_ports = [""]

        for p in ports:

            if (format(p.manufacturer) in manufacturers) and ("Standard Serial over Bluetooth link" not in format(p.description)):
                available_ports.append(p.device)
else:
    class AvailableCOMPorts:
        ports = serial.tools.list_ports.comports()
        available_ports = [""]

        for p in ports:
            available_ports.append(p.device)

@BaseRegistry.no_registration
class SerialDevice(Device):

    CONFIG_SCHEMA = vol.Schema(
        {
            vol.Required(
                "com_port",
                description="Cổng COM cho đèn USB",
                default="",
            ): vol.In(list(AvailableCOMPorts.available_ports)),
            vol.Required(
                "baudrate", description="tốc độ truyền", default=115200
            ): vol.All(int, vol.Range(min=115200)),
        }
    )

    MAX_RETRIES = 5  # Maximum number of reconnection attempts

    def __init__(self, wls, config):
        # Load previous config if exists
        try:
            with open(self.CONFIG_FILE, 'r') as f:
                prev_config = json.load(f)
                self.pid = prev_config.get('pid')
                self.vid = prev_config.get('vid')
        except FileNotFoundError:
            self.pid = None
            self.vid = None

        super().__init__(wls, config)
        self.serial = None
        self.baudrate = self._config["baudrate"]
        self.com_port = self._config["com_port"]
        # Map pid and vid to com_port
        self.pid_vid_map = {}
        for p in serial.tools.list_ports.comports():
            self.pid_vid_map[(p.pid, p.vid)] = p.device
            if p.device == self.com_port:
                self.pid = p.pid
                self.vid = p.vid
                break

    def establish_connection(self):
        try:
            self.serial = serial.Serial(self.com_port, self.baudrate, timeout=1)  # Added timeout
            if self.serial.isOpen():
                super().activate()
        except serial.SerialException as e:
            print(f'Serial Exception: {e}')

    def reconnect(self):
        retries = 0
        while retries < self.MAX_RETRIES:
            if self.serial and self.serial.isOpen():
                self.serial.close()
            for p in serial.tools.list_ports.comports():
                if p.pid == self.pid and p.vid == self.vid:
                    self.com_port = p.device
                    break
            self.establish_connection()
            if self.serial and self.serial.isOpen():
                break
            time.sleep(math.pow(2, retries))  # Exponential backoff
            retries += 1
        if retries == self.MAX_RETRIES:
            print('Max retries reached, could not reconnect.')

    def activate(self):
        if not (self.serial and self.serial.isOpen()):
            self.establish_connection()

    def deactivate(self):
        super().deactivate()
        if self.serial:
            self.serial.close()
            self.serial = None


class Devices(RegistryLoader):
    """Thin wrapper around the device registry that manages devices"""

    PACKAGE_NAME = "wls.devices"

    def __init__(self, wls):
        super().__init__(wls, Device, self.PACKAGE_NAME)

        def on_shutdown(e):
            self._zeroconf.close()
            self.deactivate_devices()

        self._wls.events.add_listener(on_shutdown, Event.WLS_SHUTDOWN)
        self._zeroconf = zeroconf.Zeroconf()

    def create_from_config(self, config):
        for device in config:
            _LOGGER.info(f"Đang tải đèn từ cấu hình: {device}")
            try:
                self._wls.devices.create(
                    id=device["id"],
                    type=device["type"],
                    config=device["config"],
                    wls=self._wls,
                )
            except vol.MultipleInvalid as e:
                _LOGGER.exception(e)

    def deactivate_devices(self):
        for device in self.values():
            device.deactivate()

    def get_device(self, device_id):
        for device in self.values():
            if device_id == device.id:
                return device
        return None

    async def async_initialize_devices(self):
        tasks = [
            device.async_initialize()
            for device in self.values()
            if hasattr(device, "async_initialize")
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if type(result) is ValueError:
                _LOGGER.warning(result)

    async def add_new_device(self, device_type, device_config):
        """
        Creates a new device.
        """
        # First, we try to make sure this device doesn't share a destination with any existing device
        if "ip_address" in device_config.keys():
            device_ip = device_config["ip_address"]
            try:
                resolved_dest = await resolve_destination(
                    self._wls.loop, self._wls.thread_executor, device_ip
                )
            except ValueError:
                _LOGGER.error(f"Loại bỏ thiết bị {device_ip}")
                return

            for existing_device in self._wls.devices.values():
                if "ip_address" in existing_device.config.keys() and (
                    existing_device.config["ip_address"] == device_ip
                    or existing_device.config["ip_address"] == resolved_dest
                ):
                    if device_type == "e131":
                        # check the universes for e131, it might still be okay at a shared ip_address
                        # eg. for multi output controllers
                        if (
                            device_config["universe"]
                            == existing_device.config["universe"]
                        ):
                            msg = f"Bỏ qua đèn {device_ip}: Chia sẻ IP và Universe đầu tiên với đèn hiện có là {existing_device.name}"
                            _LOGGER.info(msg)
                            raise ValueError(msg)
                    elif device_type == "openrgb":
                        # check the OpenRGB ID for OpenRGB device, it might still be okay at a shared ip_address
                        # eg. for multi OpenRGB devices
                        if (
                            device_config["openrgb_id"]
                            == existing_device.config["openrgb_id"]
                        ):
                            msg = f"Bỏ qua đèn {device_ip}: Chia sẻ IP và ID openrgb với đèn hiện có là {existing_device.name}"
                            _LOGGER.info(msg)
                            raise ValueError(msg)
                    else:
                        msg = f"Bỏ qua đèn {device_ip}: Chia sẻ điểm đến với đèn hiện có {existing_device.name}"
                        _LOGGER.info(msg)
                        raise ValueError(msg)

        # If RML device, get all the necessary config from the device itself
        if device_type == "rml":
            rml = RML(resolved_dest)
            rml_config = await rml.get_config()

            led_info = rml_config["leds"]
            rml_name = rml_config['name']

            rml_count = led_info["count"]
            rml_rgbmode = led_info["rgbw"]
            rml_build = rml_config["vid"]

            if rml_support_DDP(rml_build):
                _LOGGER.info(f"RML build Supports DDP: {rml_build}")
                sync_mode = "DDP"
            else:
                _LOGGER.info(
                    f"RML build pre DDP, default to UDP: {rml_build}"
                )
                sync_mode = "UDP"

            rml_config = {
                "name": rml_name,
                "pixel_count": rml_count,
                "icon_name": "rml",
                "rgbw_led": rml_rgbmode,
                "sync_mode": sync_mode,
            }

            device_config.update(rml_config)

        device_id = generate_id(device_config["name"])

        # Create the device
        _LOGGER.info(
            "Đang thêm đèn loại {} với cấu hình {}".format(
                device_type, device_config
            )
        )
        device = self._wls.devices.create(
            id=device_id,
            type=device_type,
            config=device_config,
            wls=self._wls,
        )

        if hasattr(device, "async_initialize"):
            await device.async_initialize()

        device_config = device.config
        if device_type == "rml" and rml_name is not None:
            device_config["name"] = rml_name
        # Update and save the configuration
        self._wls.config["devices"].append(
            {
                "id": device.id,
                "type": device.type,
                "config": device_config,
            }
        )

        # Generate virtual configuration for the device
        _LOGGER.info(f"Tạo đèn ảo từ đèn {device.name}")
        virtual_id = generate_id(device.name)
        virtual_config = {
            "name": device.name,
            "icon_name": device_config["icon_name"],
        }
        segments = [[device.id, 0, device_config["pixel_count"] - 1, False]]

        # Create the virtual
        virtual = self._wls.virtuals.create(
            id=virtual_id,
            config=virtual_config,
            wls=self._wls,
            is_device=device.id,
        )

        # Create the device as a single segment on the virtual
        virtual.update_segments(segments)

        # Update the configuration
        self._wls.config["virtuals"].append(
            {
                "id": virtual.id,
                "config": virtual.config,
                "segments": virtual.segments,
                "is_device": device.id,
            }
        )

        self._wls.events.fire_event(DeviceCreatedEvent(device.name))

        # Finally, save the config to file!
        save_config(
            config=self._wls.config,
            config_dir=self._wls.config_dir,
        )

        return device

    async def set_rmls_sync_mode(self, mode):
        for device in self.values():
            if (
                device.type == "rml"
                and device.pixel_count > 480
                and device.config["sync_mode"] != mode
            ):
                device.rml.set_sync_mode(mode)
                await device.rml.flush_sync_settings()
                device.update_config({"sync_mode": mode})

    async def find_rml_devices(self):
        # Scan the LAN network that match RML using zeroconf - Multicast DNS
        # Service Discovery Library
        _LOGGER.info("Đang tìm đèn...")
        rml_listener = RMLListener(self._wls)
        rmlbrowser = self._zeroconf.add_service_listener(
            "_rml._tcp.local.", rml_listener
        )
        try:
            await asyncio.sleep(30)
        finally:
            _LOGGER.info("Đã tìm xong")
            self._zeroconf.remove_service_listener(rml_listener)


class RMLListener(zeroconf.ServiceBrowser):
    def __init__(self, _wls):
        self._wls = _wls

    def remove_service(self, zeroconf_obj, type, name):
        _LOGGER.info(f"Dịch vụ {name} đã bị loại bỏ")

    def add_service(self, zeroconf_obj, type, name):
        info = zeroconf_obj.get_service_info(type, name)

        if info:
            hostname = str(info.server).rstrip(".")
            _LOGGER.info(f"Đã tìm thấy đèn: {hostname}")

            device_type = "rml"
            device_config = {"ip_address": hostname}

            def handle_exception(future):
                # Ignore exceptions, these will be raised when a device is found that already exists
                exc = future.exception()

            async_fire_and_forget(
                self._wls.devices.add_new_device(device_type, device_config),
                loop=self._wls.loop,
                exc_handler=handle_exception,
            )

    def update_service(self, zeroconf_obj, type, name):
        """Callback when a service is updated."""
        pass
