import asyncio
import logging
import sys
import os
import threading
import time
import warnings
import webbrowser
import subprocess
if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes
    import winreg
    import tkinter as tk
    from tkinter import messagebox
elif sys.platform == "darwin":
    import shutil
    from AppKit import NSWorkspace, NSObject, NSDistributedNotificationCenter

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
    GlobalPauseEvent,
    GlobalResumeEvent,
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

if sys.platform == "win32":
    WM_QUERYENDSESSION = 0x0011
    WM_ENDSESSION = 0x0016
    WM_POWERBROADCAST = 0x0218
    PBT_APMSUSPEND = 0x0004
    PBT_APMRESUMEAUTOMATIC = 0x0012
    # PBT_APMRESUMESUSPEND = 0x0007
    # PBT_APMRESUMESTANDBY = 0x0008

    class WNDCLASS(ctypes.Structure):
        _fields_ = [
            ("style", ctypes.c_uint),
            ("lpfnWndProc", ctypes.c_void_p),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", ctypes.c_void_p),
            ("hIcon", ctypes.c_void_p),
            ("hCursor", ctypes.c_void_p),
            ("hbrBackground", ctypes.c_void_p),
            ("lpszMenuName", ctypes.c_wchar_p),
            ("lpszClassName", ctypes.c_wchar_p)
        ]

    class WindowsEventHandler:
        def __init__(self, wls_core):
            self.wls_core = wls_core
            self.loop = wls_core.loop
            self.hwnd = None
            self.running = True

            # Setup Windows message thread
            self.win_thread = threading.Thread(target=self._windows_message_loop, daemon=True)

        def start(self):
            """Start the Windows event handler"""
            self.win_thread.start()
            _LOGGER.debug("Lắng nghe sự kiện Windows đã bật")

        def stop(self):
            """Stop the Windows event handler"""
            self.running = False
            if self.hwnd:
                ctypes.windll.user32.PostQuitMessage(0)
            _LOGGER.debug("Lắng nghe sự kiện Windows đã tắt")

        def _windows_message_loop(self):
            """Windows message loop running in separate thread"""
            try:
                # Register window class
                wc = self._create_window_class()
                ctypes.windll.user32.RegisterClassW(ctypes.byref(wc))

                # Create window
                self.hwnd = ctypes.windll.user32.CreateWindowExW(
                    0, wc.lpszClassName, "Event Window",
                    0, 0, 0, 0, 0, None, None, None, None
                )

                if self.hwnd:
                    _LOGGER.debug("Cửa sổ đã được tạo thành công")

                # Message loop
                msg = wintypes.MSG()
                while self.running:
                    result = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), self.hwnd, 0, 0)
                    if result == 0:  # WM_QUIT
                        break

                    ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                    ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

            except Exception as e:
                _LOGGER.error(f"Error in Windows message loop: {e}")

        def _create_window_class(self):
            """Create Windows class structure"""
            wc = WNDCLASS()
            wc.lpfnWndProc = ctypes.cast(
                ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int, ctypes.c_uint, ctypes.c_long, ctypes.c_long)(
                    self._window_proc
                ),
                ctypes.c_void_p
            )
            wc.lpszClassName = "EventHandler"
            return wc

        def _window_proc(self, hwnd, msg, wparam, lparam):
            """Window procedure callback"""
            try:
                if msg == WM_QUERYENDSESSION:
                    _LOGGER.debug("Hệ thống đang tắt hoặc đăng xuất")

                    # Tạo một event để chờ hoàn tất xử lý
                    event_done = threading.Event()

                    def process_pause():
                        _LOGGER.debug("Bắt đầu xử lý GlobalPauseEvent()")
                        self.wls_core.events.fire_event(GlobalPauseEvent())

                        # Giả lập chờ cho đến khi quá trình fire_event thực sự hoàn tất
                        time.sleep(2)  # Chờ 2 giây hoặc điều chỉnh theo yêu cầu

                        _LOGGER.debug("Đã xử lý xong GlobalPauseEvent()")
                        event_done.set()  # Đánh dấu hoàn thành

                    # Khởi chạy thread nhưng phải đảm bảo xử lý xong trước khi tiếp tục
                    thread = threading.Thread(target=process_pause, daemon=True)
                    thread.start()

                    # Chờ tối đa 5 giây để đảm bảo `fire_event()` hoàn tất
                    event_done.wait(timeout=5)

                    return 0  # Chấp nhận thoát ứng dụng sau khi xử lý xong

                elif msg == WM_ENDSESSION:
                    if wparam:  # Session đang kết thúc
                        _LOGGER.debug("Chấp nhận thoát ứng dụng")
                        return 0

                elif msg == WM_POWERBROADCAST:
                    if wparam == PBT_APMSUSPEND:
                        _LOGGER.debug("Hệ thống đang vào chế độ ngủ.")
                        self.wls_core.events.fire_event(GlobalPauseEvent())
                    elif wparam == PBT_APMRESUMEAUTOMATIC:
                        self.wls_core.events.fire_event(GlobalResumeEvent())
                        _LOGGER.debug("Hệ thống đã thức dậy từ chế độ ngủ.")

            except Exception as e:
                _LOGGER.error(f"Error in window procedure: {e}")

            return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)
else:
    class MacOSEventHandler:
        def __init__(self, wls_core):
            self.wls_core = wls_core
            self.loop = wls_core.loop
            self.running = True

            # Workspace notifications
            self.workspace = NSWorkspace.sharedWorkspace()
            self.ws_notification_center = self.workspace.notificationCenter()

            # Distributed notifications for lock/unlock
            self.dist_notification_center = NSDistributedNotificationCenter.defaultCenter()

            # Create observer object
            self.observer = MacOSEventObserver.alloc().initWithHandler_(self)

            # For cleanup
            self.registered_notifications = []

        def start(self):
            """Start the MacOS event handler"""
            try:
                # Workspace notifications
                self._register_notification(
                    self.ws_notification_center,
                    'handleSleepNotification:',
                    'NSWorkspaceWillSleepNotification'
                )

                self._register_notification(
                    self.ws_notification_center,
                    'handleWakeNotification:',
                    'NSWorkspaceDidWakeNotification'
                )

                self._register_notification(
                    self.ws_notification_center,
                    'handleShutdownNotification:',
                    'NSWorkspaceWillPowerOffNotification'
                )

                # Distributed notifications
                self._register_notification(
                    self.dist_notification_center,
                    'handleLogOffNotification:',
                    'com.apple.sessionDidLogout'
                )

                # self._register_notification(
                    # self.dist_notification_center,
                    # 'handleScreenLockNotification:',
                    # 'com.apple.screenIsLocked'
                # )

                # self._register_notification(
                    # self.dist_notification_center,
                    # 'handleScreenUnlockNotification:',
                    # 'com.apple.screenIsUnlocked'
                # )

                _LOGGER.debug("MacOS event listener started successfully")

            except Exception as e:
                _LOGGER.error(f"Failed to start MacOS event listener: {e}")

        def _register_notification(self, center, selector, name):
            """Helper to register notifications and track them for cleanup"""
            center.addObserver_selector_name_object_(
                self.observer,
                selector,
                name,
                None
            )
            self.registered_notifications.append((center, name))

        def stop(self):
            """Stop the MacOS event handler"""
            try:
                self.running = False

                # Clean up all registered notifications
                for center, name in self.registered_notifications:
                    center.removeObserver_name_object_(self.observer, name, None)

                self.registered_notifications.clear()

                _LOGGER.debug("MacOS event listener stopped successfully")

            except Exception as e:
                _LOGGER.error(f"Error stopping MacOS event listener: {e}")

        def _handle_event(self, pause, component="THREAD"):
            """Common event handling with timeout"""
            try:
                if component == "THREAD":
                    event = threading.Event()

                    def process_event():
                        _LOGGER.debug(f"Processing {'pause' if pause else 'resume'} event")
                        if pause:
                            self.wls_core.events.fire_event(GlobalPauseEvent())
                        else:
                            self.wls_core.events.fire_event(GlobalResumeEvent())
                        time.sleep(2.0)  # Allow time for event processing
                        _LOGGER.debug("Event processed")
                        event.set()

                    # Run in thread to avoid blocking
                    thread = threading.Thread(target=process_event, daemon=True)
                    thread.start()

                    # Wait with timeout
                    if not event.wait(timeout=5.0):
                        _LOGGER.warning("Event processing timed out")
                else:
                    _LOGGER.debug(f"Processing {'pause' if pause else 'resume'} event for {component}")
                    if pause:
                        self.wls_core.events.fire_event(GlobalPauseEvent())
                    else:
                        self.wls_core.events.fire_event(GlobalResumeEvent())
                    _LOGGER.debug("Event processed")

            except Exception as e:
                _LOGGER.error(f"Error handling event: {e}")

    class MacOSEventObserver(NSObject):
        """Observer class to handle MacOS notifications"""

        def initWithHandler_(self, handler):
            self = self.init()
            self.handler = handler
            return self

        def handleSleepNotification_(self, notification):
            _LOGGER.debug("Sleep notification received")
            if self.handler:
                self.handler._handle_event(pause=True)

        def handleWakeNotification_(self, notification):
            _LOGGER.debug("Wake notification received")
            if self.handler:
                self.handler._handle_event(pause=False)

        def handleShutdownNotification_(self, notification):
            _LOGGER.debug("Shutdown notification received")
            if self.handler:
                self.handler._handle_event(pause=True, component="THREAD")

        def handleLogOffNotification_(self, notification):
            _LOGGER.debug("Log Off notification received")
            if self.handler:
                self.handler._handle_event(pause=True, component="THREAD")

        # def handleScreenLockNotification_(self, notification):
            # _LOGGER.debug("Screen lock notification received")
            # if self.handler:
                # self.handler._handle_event(pause=True)

        # def handleScreenUnlockNotification_(self, notification):
            # _LOGGER.debug("Screen unlock notification received")
            # if self.handler:
                # self.handler._handle_event(pause=False)


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

        if sys.platform == "win32":
            self.event_handler = WindowsEventHandler(self)
        else:
            self.event_handler = MacOSEventHandler(self)

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

    def restore(self):
        if sys.platform == "win32":
            # Tạo cửa sổ gốc ẩn
            root = tk.Tk()
            root.withdraw()  # Ẩn cửa sổ gốc

            # Hiển thị hộp thoại xác nhận với biểu tượng cảnh báo và các nút Yes/No
            result = messagebox.askyesno(
                title="Xác nhận",
                message="Bạn có chắc chắn muốn khôi phục về mặc định không nếu mọi cài đặt trước đây của bạn sẽ bị xoá?",
                icon='warning'
            )

            # Nếu người dùng nhấn Yes
            if result:
                path_restore = os.path.join(os.environ["ProgramFiles"], "Rainbow Music Led\\bin", "restore.exe")

                try:
                    # Chạy chương trình restore.exe với cửa sổ ẩn
                    subprocess.Popen(
                        [path_restore],
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=subprocess.CREATE_NO_WINDOW  # Chỉ hoạt động trên Windows
                    )

                    self.stop(0)
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể chạy chương trình: {e}")

            root.destroy()
        else:
            # Lấy thư mục home của người dùng
            home_dir = os.path.expanduser("~")
            aw_dest_path = os.path.join(home_dir, ".rmlapp")
            wls_dest_path = os.path.join(home_dir, ".wls")

            # Xóa thư mục .rmlapp nếu nó tồn tại
            if os.path.exists(aw_dest_path) and os.path.isdir(aw_dest_path):
                shutil.rmtree(aw_dest_path)

            # Xóa thư mục .wls nếu nó tồn tại
            if os.path.exists(wls_dest_path) and os.path.isdir(wls_dest_path):
                shutil.rmtree(wls_dest_path)

            self.stop_aw(0)

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
            MenuItem("Khôi phục về cài đặt gốc | Restore to default", self.restore),
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
            MenuItem("Khôi phục về cài đặt gốc | Restore to default", self.restore),
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

        if self.event_handler:
            self.event_handler.start()

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

            _LOGGER.info("Stopping HTTP Server...")
            await self.http.stop()

        except Exception as e:
            _LOGGER.error(f"An error occurred while stopping: {e}")
            self.exit_code = 1

        finally:
            self.thread_executor.shutdown()
            if self.exit_code != 1:
                self.exit_code = exit_code
            self.loop.stop()

    async def async_stop(self, exit_code):
        if self.event_handler:
            self.event_handler.stop()

        return await self._common_async_stop(exit_code)

    async def async_stop_aw(self, exit_code):
        exit_code = await self._common_async_stop(exit_code)

        if sys.platform == "win32":
            path_rmlapp = os.path.join(os.environ["ProgramFiles"], "Rainbow Music Led\\bin", "rmlapp.exe")
            startupinfo = subprocess.STARTUPINFO()
            subprocess.Popen([path_rmlapp], startupinfo=startupinfo)
        elif sys.platform == "darwin":
            subprocess.run(['open', '/Applications/rmlapp.app'], check=True)

        return exit_code
