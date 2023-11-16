import asyncio
import logging
import sys
import os
import time
import warnings
import webbrowser
import subprocess
from concurrent.futures import ThreadPoolExecutor

from wls.color import (
    WLS_COLORS,
    WLS_GRADIENTS,
    parse_color,
    parse_gradient,
    validate_color,
    validate_gradient,
)
from wls.config import get_ssl_certs, load_config, save_config
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
    def __init__(
        self,
        config_dir,
        host=None,
        port=None,
        port_s=None,
        icon=None,
    ):
        self.icon = icon
        self.config_dir = config_dir
        self.config = load_config(config_dir)
        self.config["wls_presets"] = wls_presets
        self.host = host if host else self.config["host"]
        self.port = port if port else self.config["port"]
        self.port_s = port_s if port_s else self.config["port_s"]

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
            self.setup_icon_menu()

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
            url = f"http://127.0.0.1:{str(self.port)}"
        else:
            # If the user has specified an adaptor, launch its address
            url = self.http.base_url
        try:
            webbrowser.get().open(url)
        except webbrowser.Error:
            _LOGGER.warning(
                f"Không mở được trình duyệt web mặc định. Để truy cập giao diện web của WiFi Led Studio, hãy mở {url} trong trình duyệt. Để tránh lỗi này trong tương lai, hãy cài mặc định trình duyệt cho hệ thống của bạn."
            )

    def open_app(self):
        if sys.platform == "win32":
            path1 = os.path.join(os.environ["ProgramFiles"], "Ambilight WiFi-USB\\bin", "_ambilightwifi_.exe")
            path2 = os.path.join(os.environ["ProgramFiles"], "AmbilightWiFi\\bin", "ambilightwifi.exe")
            
            if os.path.exists(path1):
                subprocess.call(path1)
            elif os.path.exists(path2):
                subprocess.call(path2)
            else:
                print("Neither path1 nor path2 exists.")
        elif sys.platform == "darwin":
            subprocess.run(['open', '/Applications/Ambilight WiFi-USB.app'], check=True)
        else:
            subprocess.run(['open', '/Applications/Ambilight WiFi-USB.app'], check=True)

    def restart_wls(self):
        if sys.platform == "win32":
            path = os.path.join(os.environ["ProgramFiles"], "WiFi Led Studio", "wifiledstudio.exe")
            subprocess.call(path)
        elif sys.platform == "darwin":
            subprocess.run(['open', '/Applications/WiFi Led Studio.app'], check=True)
        else:
            subprocess.run(['open', '/Applications/WiFi Led Studio.app'], check=True)

    def setup_icon_menu(self):
        import pystray

        self.icon.menu = pystray.Menu(
            pystray.MenuItem("Mở", self.open_ui, default=True),
            pystray.MenuItem("Theo màu màn hình", self.open_app),
            pystray.MenuItem("Khởi động lại", self.restart_wls),
            pystray.MenuItem("Thoát", self.stop),
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

    def start(self, open_ui=False):
        async_fire_and_forget(self.async_start(open_ui=open_ui), self.loop)

        # Windows does not seem to handle Ctrl+C well so as a workaround
        # register a handler and manually stop the app
        if sys.platform == "win32":
            import win32api

            def handle_win32_interrupt(sig, func=None):
                self.stop(exit_code=2)
                return True

            win32api.SetConsoleCtrlHandler(handle_win32_interrupt, 1)

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

    async def async_start(self, open_ui=False):
        _LOGGER.info("Khởi động WiFi Led Studio")
        await self.http.start(get_ssl_certs(config_dir=self.config_dir))
        if (
            self.icon is not None
            and self.icon.notify is not None
            and self.icon.HAS_NOTIFICATION
        ):
            self.icon.notify(
                "Đã khởi động WiFi Led Studio.\nSử dụng biểu tượng trái tim ở Taskbar để mở.", "WiFi Led Studio @ Rainbow Music Led"
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

        # sync_mode = RML_CONFIG_SCHEMA(self.config["rml_preferences"])[
        #     "rml_preferred_mode"
        # ]
        # if sync_mode:
        #     await self.devices.set_rmls_sync_mode(sync_mode)

        self.virtuals.create_from_config(self.config["virtuals"])
        self.integrations.create_from_config(self.config["integrations"])

        if self.config["scan_on_startup"]:
            async_fire_and_forget(self.devices.find_rml_devices(), self.loop)

        async_fire_and_forget(
            self.integrations.activate_integrations(), self.loop
        )

        if open_ui:
            self.open_ui()

        await self.flush_loop()

    def stop(self, exit_code):
        async_fire_and_forget(self.async_stop(exit_code), self.loop)

    async def async_stop(self, exit_code):
        if not self.loop:
            return

        print("Dừng WiFi Led Studio.")

        # 1 = Error
        # 2 = Direct User Input
        # 3 = API Request (shutdown)
        # 4 = Restart (stop then restart wls core)

        if exit_code == 1:
            _LOGGER.info("Đã gặp lỗi. Đang Tắt.")
        if exit_code == 2:
            _LOGGER.info("Bàn phím WiFi Led Studio bị gián đoạn. Đang Tắt.")
        if exit_code == 3:
            _LOGGER.info("Yêu cầu tắt WiFi Led Studio thông qua API. Đang Tắt.")
        if exit_code == 4:
            _LOGGER.info("WiFi Led Studio đang khởi động lại.")

        # Fire a shutdown event and flush the loop
        self.events.fire_event(WlsShutdownEvent())
        await asyncio.sleep(0)

        _LOGGER.info("Dừng HttpServer...")
        await self.http.stop()

        # Cancel all the remaining task and wait
        _LOGGER.info("Buộc tắt các nhiệm vụ còn lại...")
        tasks = [
            task
            for task in asyncio.all_tasks()
            if task is not asyncio.current_task()
        ]
        list(map(lambda task: task.cancel(), tasks))

        # Save the configuration before shutting down
        save_config(config=self.config, config_dir=self.config_dir)

        _LOGGER.info("Flushing loop...")
        await self.flush_loop()
        self.thread_executor.shutdown()
        self.exit_code = exit_code
        self.loop.stop()
        return exit_code
