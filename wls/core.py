import asyncio
import logging
import sys
import os
import time
import warnings
import webbrowser
import subprocess
if sys.platform == "win32":
    import winreg
elif sys.platform == "darwin":
    import shutil

from pystray import Menu, MenuItem
from concurrent.futures import ThreadPoolExecutor

from wls.color import (
    WLS_COLORS,
    WLS_GRADIENTS,
    parse_color,
    parse_gradient,
    validate_color,
    validate_gradient,
)
from wls.config import get_ssl_certs, create_backup, load_config, remove_virtuals_active_effects, save_config
from wls.devices import Devices
from wls.effects import Effects
from wls.effects.math import interpolate_pixels
from wls.events import (
    Event,
    Events,
    WlsShutdownEvent,
    VisualisationUpdateEvent,
)
from wls.http_manager import HttpServer
from wls.integrations import Integrations
from wls.mdns_manager import ZeroConfRunner
from wls.presets import wls_presets
from wls.scenes import Scenes
from wls.utils import (
    RollingQueueHandler,
    UserDefaultCollection,
    async_fire_and_forget,
    currently_frozen,
)
from wls.virtuals import Virtuals

_LOGGER = logging.getLogger(__name__)
if currently_frozen():
    warnings.filterwarnings("ignore")


class WlsCore:

    EXIT_CODES = {
        1: "WiFi Led Studio encountered an error - Shutting down.",
        2: "Keyboard interrupt - Shutting down.",
        3: "Shutdown request via API - Shutting down.",
        4: "Restart request via API - Restarting.",
        5: "Shutdown request via CI testing flag - Shutting down.",
    }

    def __init__(
        self,
        config_dir,
        host=None,
        port=None,
        port_s=None,
        icon=None,
        ci_testing=False,
        clear_config=False,
        clear_effects=False,
    ):
        self.icon = icon
        self.config_dir = config_dir

        if clear_config:
            _LOGGER.warning("Clearing WiFi Led Studio config.")
            create_backup(config_dir, "DELETE")

        self.config = load_config(config_dir)

        if clear_effects:
            _LOGGER.warning("Clearing active effects.")
            remove_virtuals_active_effects(self.config)

        self.config["wls_presets"] = wls_presets
        self.host = host if host else self.config["host"]
        self.port = port if port else self.config["port"]
        self.port_s = port_s if port_s else self.config["port_s"]
        self.ci_testing = ci_testing
        if sys.platform == "win32":
            self.loop = asyncio.ProactorEventLoop()
        else:
            try:
                import uvloop

                self.loop = uvloop.new_event_loop()
            except ImportError as error:
                _LOGGER.info("Reverting to asyncio loop.")
                self.loop = asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)

        # self.loop.set_debug(True)

        self.thread_executor = ThreadPoolExecutor()
        self.loop.set_default_executor(self.thread_executor)
        self.loop.set_exception_handler(self.loop_exception_handler)
        if self.icon:
            if self.check_rmlapp_run_key():
                self.setup_icon_menu_aw()
            else:
                self.setup_icon_menu_wls()

        self.setup_logqueue()
        self.events = Events(self)
        self.setup_visualisation_events()
        self.http = HttpServer(
            wls=self, host=self.host, port=self.port, port_s=self.port_s
        )
        self.exit_code = None

    def dev_enabled(self):
        return self.config["dev_mode"]

    def loop_exception_handler(self, loop, context):
        kwargs = {}
        exception = context.get("exception")
        if exception:
            kwargs["exc_info"] = (
                type(exception),
                exception,
                exception.__traceback__,
            )

        _LOGGER.error(
            "Ngoại lệ trong vòng lặp sự kiện cốt lõi: {}".format(context["message"]),
            **kwargs,
        )

    def open_ui(self):
        # Check if we're binding to all adaptors
        if str(self.config["host"]) == "0.0.0.0":
            url = f"http://localhost:{str(self.port)}"
        else:
            # If the user has specified an adaptor, launch its address
            url = self.http.base_url
        try:
            webbrowser.get().open(url)
        except webbrowser.Error:
            _LOGGER.warning(
                f"Không mở được trình duyệt web mặc định. Để truy cập giao diện web của WiFi Led Studio, hãy mở {url} trong trình duyệt. Để tránh lỗi này trong tương lai, hãy cài mặc định trình duyệt cho hệ thống của bạn."
            )

    def restart_wls(self):
        self.stop(exit_code=4)

    def check_rmlapp_run_key(self):
        if sys.platform == "win32":
            # Mở key HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")

            # Lấy số lượng giá trị trong key
            num_values = winreg.QueryInfoKey(key)[1]

            # Duyệt qua từng giá trị trong key
            for i in range(num_values):
                value_name, _, _ = winreg.EnumValue(key, i)
                if value_name == "A-Rainbow Music Led":
                    # Tìm thấy key "A-Rainbow Music Led"
                    winreg.CloseKey(key)
                    return True

            # Không tìm thấy key "A-Rainbow Music Led"
            winreg.CloseKey(key)
            return False
        elif sys.platform == "darwin":
            file_path = os.path.expanduser('~/Library/LaunchAgents/com.rmlapp.startup.plist')
            # Kiểm tra hàm
            if os.path.isfile(file_path):
                return True
            else:
                return False

    def delete_wls_key(self):
        if sys.platform == "win32":
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(key, "A-WiFi Led Studio")
        elif sys.platform == "darwin":
            wls_destination_path = os.path.expanduser('~/Library/LaunchAgents/com.wls.startup.plist')
            os.remove(wls_destination_path)

    def delete_aw_key(self):
        if sys.platform == "win32":
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            winreg.DeleteValue(key, "A-Rainbow Music Led")
        elif sys.platform == "darwin":
            aw_destination_path = os.path.expanduser("~/Library/LaunchAgents/com.rmlapp.startup.plist")
            os.remove(aw_destination_path)

    def add_wls_key(self):
        if sys.platform == "win32":
            path1 = os.path.join(os.environ["ProgramFiles"], "Rainbow Music Led\\WiFi Led Studio", "WiFi Led Studio.exe")
            path2 = '"' + path1 + '"'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "A-WiFi Led Studio", 0, winreg.REG_SZ, path2)
            winreg.CloseKey(key)
        elif sys.platform == "darwin":
            wls_source_path = "/Applications/rmlapp.app/Contents/Resources/com.wls.startup.plist"
            wls_destination_path = os.path.expanduser("~/Library/LaunchAgents/com.wls.startup.plist")

            shutil.copy(wls_source_path, wls_destination_path)

    def add_aw_key(self):
        if sys.platform == "win32":
            path1 = os.path.join(os.environ["ProgramFiles"], "Rainbow Music Led\\bin", "rmlapp.exe")
            path2 = '"' + path1 + '"'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            winreg.SetValueEx(key, "A-Rainbow Music Led", 0, winreg.REG_SZ, path2)
            winreg.CloseKey(key)
        elif sys.platform == "darwin":
            aw_source_path = "/Applications/rmlapp.app/Contents/Resources/com.rmlapp.startup.plist"
            aw_destination_path = os.path.expanduser("~/Library/LaunchAgents/com.rmlapp.startup.plist")

            shutil.copy(aw_source_path, aw_destination_path)

    global adapter

    def setup_icon_menu_aw(self):
        adapter = "Bấm để sáng 'hiệu ứng màu' khi khởi động | Enable autostart 'Effect / Color'"
        if not self.check_rmlapp_run_key():
            self.delete_wls_key()
            self.add_aw_key()

        self.icon.menu = Menu(
            MenuItem(lambda text: adapter, self.setup_icon_menu_wls),
            Menu.SEPARATOR,
            MenuItem("Mở trang điều khiển | Open Web-App", self.open_ui, default=True),
            MenuItem("Theo màu màn hình | Screen capture", self.stop_aw),
            Menu.SEPARATOR,
            MenuItem("Khởi động lại | Restart", self.restart_wls),
            MenuItem("Thoát | Quit", self.stop),
        )

    def setup_icon_menu_wls(self):
        adapter = "Bấm để 'theo màu màn hình' khi khởi động | Enable autostart 'Screen capture'"
        if self.check_rmlapp_run_key():
            self.delete_aw_key()
            self.add_wls_key()

        self.icon.menu = Menu(
            MenuItem(lambda text: adapter, self.setup_icon_menu_aw),
            Menu.SEPARATOR,
            MenuItem("Mở trang điều khiển | Open Web-App", self.open_ui, default=True),
            MenuItem("Theo màu màn hình | Screen capture", self.stop_aw),
            Menu.SEPARATOR,
            MenuItem("Khởi động lại | Restart", self.restart_wls),
            MenuItem("Thoát | Quit", self.stop),
        )

    def setup_visualisation_events(self):
        """
        creates event listeners to fire visualisation events at
        a given rate
        """
        min_time_since = 1 / self.config["visualisation_fps"]
        time_since_last = {}
        max_len = self.config["visualisation_maxlen"]

        def handle_visualisation_update(event):
            is_device = event.event_type == Event.DEVICE_UPDATE
            time_now = time.time()

            if is_device:
                vis_id = getattr(event, "device_id")
            else:
                vis_id = getattr(event, "virtual_id")

            try:
                time_since = time_now - time_since_last[vis_id]
                if time_since < min_time_since:
                    return
            except KeyError:
                pass

            time_since_last[vis_id] = time_now

            pixels = event.pixels

            if len(pixels) > max_len:
                pixels = interpolate_pixels(pixels, max_len)

            self.events.fire_event(
                VisualisationUpdateEvent(is_device, vis_id, pixels)
            )

        self.events.add_listener(
            handle_visualisation_update,
            Event.VIRTUAL_UPDATE,
        )

        self.events.add_listener(
            handle_visualisation_update,
            Event.DEVICE_UPDATE,
        )

    def setup_logqueue(self):
        def log_filter(record):
            return (record.name != "wls.api.log") and (record.levelno >= 20)

        self.logqueue = asyncio.Queue(maxsize=100)
        logqueue_handler = RollingQueueHandler(self.logqueue)
        logqueue_handler.addFilter(log_filter)
        root_logger = logging.getLogger()
        root_logger.addHandler(logqueue_handler)

    async def flush_loop(self):
        await asyncio.sleep(0)

    def start(self, open_ui=False, pause_all=False):
        async_fire_and_forget(
            self.async_start(open_ui=open_ui, pause_all=pause_all), self.loop
        )

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            self.loop.call_soon(
                self.loop.create_task, self.async_stop(exit_code=1)
            )
            self.loop.run_forever()
        except BaseException:
            # Catch all other exceptions and terminate the application. The loop
            # exception handler will take care of logging the actual error and
            # Wls will cleanly shutdown.
            self.loop.run_until_complete(self.async_stop(exit_code=1))
            pass
        finally:
            self.loop.stop()

        return self.exit_code

    async def async_start(self, open_ui=False, pause_all=False):
        _LOGGER.info("Khởi động WiFi Led Studio")
        await self.http.start(get_ssl_certs(config_dir=self.config_dir))
        if (
            self.icon is not None
            and self.icon.notify is not None
            and self.icon.HAS_NOTIFICATION
        ):
            self.icon.notify(
                "Bạn ơi, tôi ở dưới đây!\nBấm vào biểu tượng ở khay hệ thống để chọn hiệu ứng nhé", "Nháy theo nhạc, màu đơn, hiệu ứng màu"
            )
        self.devices = Devices(self)
        self.effects = Effects(self)
        self.virtuals = Virtuals(self)
        self.integrations = Integrations(self)
        self.scenes = Scenes(self)
        self.colors = UserDefaultCollection(
            self,
            "Colors",
            WLS_COLORS,
            "user_colors",
            validate_color,
            parse_color,
        )
        self.gradients = UserDefaultCollection(
            self,
            "Gradients",
            WLS_GRADIENTS,
            "user_gradients",
            validate_gradient,
            parse_gradient,
        )

        # TODO: Deferr
        self.devices.create_from_config(self.config["devices"])
        await self.devices.async_initialize_devices()

        self.zeroconf = ZeroConfRunner(wls=self)
        self.virtuals.create_from_config(
            self.config["virtuals"], pause_all=pause_all
        )
        self.integrations.create_from_config(self.config["integrations"])

        if self.config["scan_on_startup"]:
            async_fire_and_forget(
                self.zeroconf.discover_rml_devices(), self.loop
            )

        async_fire_and_forget(
            self.integrations.activate_integrations(), self.loop
        )

        if open_ui:
            self.open_ui()

        if self.ci_testing:
            await asyncio.sleep(5)
            self.stop(5)

        if pause_all:
            # pause at the virtuals level
            self.virtuals.pause_all()

        await self.flush_loop()

    def stop(self, exit_code):
        async_fire_and_forget(self.async_stop(exit_code), self.loop)

    def stop_aw(self, exit_code):
        async_fire_and_forget(self.async_stop_aw(exit_code), self.loop)

    async def _common_async_stop(self, exit_code):
        if not self.loop:
            return

        print("Stopping WiFi Led Studio.")
        try:
            _LOGGER.info(self.EXIT_CODES.get(exit_code, "Unknown exit code."))
            self.events.fire_event(WlsShutdownEvent())
            _LOGGER.info("Stopping HTTP Server...")
            await self.http.stop()

            tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
            if tasks:
                _LOGGER.debug(f"Killing {len(tasks)} tasks prior to shutdown...")
                group = asyncio.gather(*tasks, return_exceptions=True)
                group.cancel()
                try:
                    await group
                except asyncio.CancelledError:
                    pass
                _LOGGER.debug("All tasks killed.")
            save_config(config=self.config, config_dir=self.config_dir)

        except Exception as e:
            _LOGGER.error(f"An error occurred while stopping: {e}")
            self.exit_code = 1

        finally:
            self.thread_executor.shutdown()
            if self.exit_code != 1:
                self.exit_code = exit_code
            self.loop.stop()

    async def async_stop(self, exit_code):
        return await self._common_async_stop(exit_code)

    async def async_stop_aw(self, exit_code):
        exit_code = await self._common_async_stop(exit_code)

        if sys.platform == "win32":
            path1 = os.path.join(os.environ["ProgramFiles"], "Rainbow Music Led\\bin", "rmlapp.exe")
            startupinfo = subprocess.STARTUPINFO()
            subprocess.Popen([path1], startupinfo=startupinfo)
        elif sys.platform == "darwin":
            subprocess.run(['open', '/Applications/rmlapp.app'], check=True)

        return exit_code
