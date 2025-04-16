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
        self.led_active = True  # Trạng thái LED: True = bật, False = tắt
        self.current_effect = None  # Hiệu ứng đang được chọn sẽ được cập nhật sau - sẽ được cập nhật sau khi tải cấu hình

        if clear_config:
            _LOGGER.warning("Clearing WiFi Led Studio config.")
            create_backup(config_dir, "DELETE")

        self.config = load_config(config_dir)

        if clear_effects:
            _LOGGER.warning("Clearing active effects.")
            remove_virtuals_active_effects(self.config)

        # Đọc hiệu ứng đã lưu từ cấu hình
        if "current_effect" in self.config:
            self.current_effect = self.config["current_effect"]
            _LOGGER.debug(f"Đã đọc hiệu ứng đã lưu từ cấu hình: {self.current_effect}")

        # Đọc hiệu ứng đã lưu từ cấu hình
        if "current_effect" in self.config:
            self.current_effect = self.config["current_effect"]
            _LOGGER.debug(f"Đã đọc hiệu ứng đã lưu từ cấu hình: {self.current_effect}")

        self.config["wls_presets"] = wls_presets
        self.host = host if host else self.config["host"]
        self.port = port if port else self.config["port"]
        self.port_s = port_s if port_s else self.config["port_s"]

        # Khôi phục hiệu ứng hiện tại từ cấu hình (nếu có)
        if "current_effect" in self.config:
            self.current_effect = self.config["current_effect"]
            _LOGGER.debug(f"Đã khôi phục hiệu ứng {self.current_effect} từ cấu hình")
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
            # Sử dụng phương thức mới để thiết lập menu icon
            self.setup_icon_menu()

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

    def toggle_startup_mode(self):
        """
        Toggle between 'Screen capture' and 'Effect / Color' startup modes.
        This is a more professional approach that combines the functionality
        of setup_icon_menu_aw and setup_icon_menu_wls into a single method.
        """
        # Check current state
        is_rmlapp_enabled = self.check_rmlapp_run_key()

        # Toggle state
        if is_rmlapp_enabled:
            # Switch to WLS mode
            self.delete_aw_key()
            self.add_wls_key()
            menu_text = "Khởi động máy mở 'theo màu màn hình' | Enable autostart 'Screen capture'"
        else:
            # Switch to AW mode
            self.delete_wls_key()
            self.add_aw_key()
            menu_text = "Khởi động máy mở 'hiệu ứng / màu' | Enable autostart 'Effect / Color'"

        # Update menu
        self.setup_icon_menu(toggle_text=menu_text)

    def toggle_led_state(self):
        """
        Toggle LED state between on and off.
        Uses GlobalPauseEvent and GlobalResumeEvent to control all LEDs.
        """
        if self.led_active:
            # Turn off LEDs
            self.events.fire_event(GlobalPauseEvent())
            self.led_active = False
            _LOGGER.debug("Đã tắt tất cả đèn LED")
        else:
            # Turn on LEDs
            self.events.fire_event(GlobalResumeEvent())
            self.led_active = True
            _LOGGER.debug("Đã bật tất cả đèn LED")

        # Update menu to reflect new state
        self.setup_icon_menu()

    def set_global_brightness(self, brightness_value):
        """
        Set global brightness for all LED devices.

        Args:
            brightness_value (float): Brightness value between 0.0 and 1.0
        """
        # Ensure brightness is within valid range
        brightness_value = max(0.0, min(brightness_value, 1.0))

        # Update config
        self.config["global_brightness"] = brightness_value

        # Save config
        from wls.config import save_config
        save_config(self.config, self.config_dir)

        _LOGGER.info(f"Đã đặt độ sáng toàn cục thành {int(brightness_value * 100)}%")

        # Update menu to reflect new state
        if self.icon:
            try:
                self.setup_icon_menu()
                _LOGGER.debug(f"Đã cập nhật menu sau khi thay đổi độ sáng thành {int(brightness_value * 100)}%")
            except Exception as e:
                _LOGGER.error(f"Lỗi khi cập nhật menu độ sáng: {e}")

    def apply_effect_to_all(self, effect_type):
        """
        Apply an effect to all virtual devices.

        Args:
            effect_type (str): The effect type to apply
        """
        _LOGGER.debug(f"Bắt đầu áp dụng hiệu ứng {effect_type} (type: {type(effect_type)}) cho tất cả thiết bị ảo")
        try:
            # Kiểm tra xem effect_type có trong registry không
            registry = self.effects._cls.registry()
            _LOGGER.debug(f"Registry có {len(registry)} hiệu ứng: {', '.join(registry.keys())}")

            # Nếu effect_type không có trong registry, thử tìm kiếm không phân biệt chữ hoa/thường
            if effect_type not in registry:
                _LOGGER.debug(f"Hiệu ứng {effect_type} không có trong registry, thử tìm kiếm không phân biệt chữ hoa/thường")
                for reg_effect in registry.keys():
                    if effect_type.lower() == reg_effect.lower():
                        effect_type = reg_effect
                        _LOGGER.debug(f"Đã tìm thấy hiệu ứng {effect_type} trong registry")
                        break

            # Create a new effect instance using the effects registry
            _LOGGER.debug(f"Tạo hiệu ứng {effect_type} từ registry")
            effect = self.effects.create(
                type=effect_type,
                wls=self,
                config={}  # Empty config to use defaults
            )

            # Apply to all virtuals
            _LOGGER.debug(f"Áp dụng hiệu ứng cho tất cả thiết bị ảo")
            for virtual in self.virtuals.values():
                try:
                    virtual.set_effect(effect)
                    _LOGGER.debug(f"Đã áp dụng hiệu ứng {effect_type} cho thiết bị ảo {virtual.id}")
                except Exception as e:
                    _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng {effect_type} cho thiết bị ảo {virtual.id}: {e}")
                    import traceback
                    _LOGGER.error(traceback.format_exc())

            # Lưu hiệu ứng hiện tại
            self.current_effect = effect_type

            # Lưu hiệu ứng hiện tại vào cấu hình
            try:
                self.config["current_effect"] = effect_type
                save_config(self.config, self.config_dir)
                _LOGGER.debug(f"Đã lưu hiệu ứng {effect_type} vào cấu hình")
            except Exception as e:
                _LOGGER.error(f"Lỗi khi lưu hiệu ứng vào cấu hình: {e}")

            _LOGGER.info(f"Đã áp dụng hiệu ứng {effect_type} cho tất cả thiết bị ảo")

            # Cập nhật menu để hiển thị hiệu ứng đang chọn
            if self.icon:
                try:
                    self.setup_icon_menu()
                    _LOGGER.debug(f"Đã cập nhật menu sau khi chọn hiệu ứng {effect_type}")
                except Exception as e:
                    _LOGGER.error(f"Lỗi khi cập nhật menu: {e}")

        except Exception as e:
            _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng {effect_type}: {e}")
            import traceback
            _LOGGER.error(traceback.format_exc())

        # Update menu to reflect new state
        self.setup_icon_menu()

    def setup_icon_menu(self, toggle_text=None):
        """
        Setup the icon menu with the appropriate text based on current state.

        Args:
            toggle_text: Optional text override for the toggle menu item.
                         If None, it will be determined based on current state.
        """
        if toggle_text is None:
            # Determine appropriate text based on current state
            if self.check_rmlapp_run_key():
                toggle_text = "Khởi động máy mở 'hiệu ứng / màu' | Enable autostart 'Effect / Color'"
            else:
                toggle_text = "Khởi động máy mở 'theo màu màn hình' | Enable autostart 'Screen capture'"

        # Determine LED toggle text based on current state
        led_toggle_text = "Tạm dừng | Suspend" if self.led_active else "Tiếp tục | Resume"

        # Create submenu for advanced options
        advanced_submenu = Menu(
            MenuItem("Khởi động lại | Restart", self.restart_wls),
            MenuItem("Khôi phục mặc định | Restore default", self.restore),
        )

        # Create submenu for brightness
        current_brightness = int(self.config.get("global_brightness", 1.0) * 100)

        # Tạo danh sách các mục độ sáng với dấu tích cho mục được chọn
        brightness_items = []
        for brightness in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            brightness_text = f"{brightness}%"
            if brightness == current_brightness:
                brightness_text = f"✓ {brightness_text}"
            # Tạo một hàm closure để giữ giá trị brightness
            def make_brightness_handler(value):
                return lambda: self.set_global_brightness(value/100)

            brightness_items.append(
                MenuItem(brightness_text, make_brightness_handler(brightness))
            )

        brightness_submenu = Menu(*brightness_items)

        # Create submenu for effects
        effects_items = []

        # Kiểm tra xem self.effects đã tồn tại chưa
        if not hasattr(self, 'effects') or self.effects is None:
            _LOGGER.debug("self.effects chưa được khởi tạo, bỏ qua menu hiệu ứng")
            effect_types = []
        else:
            try:
                # Get all available effects
                _LOGGER.debug("Đang tải danh sách hiệu ứng...")
                try:
                    effect_types = self.effects.types()
                    _LOGGER.debug(f"Đã tìm thấy {len(effect_types)} hiệu ứng")
                except Exception as e:
                    _LOGGER.error(f"Lỗi khi gọi self.effects.types(): {e}")
                    # Thử cách khác
                    _LOGGER.debug("Thử lấy danh sách hiệu ứng từ registry")
                    try:
                        effect_types = list(self.effects._cls.registry().keys())
                        _LOGGER.debug(f"Đã tìm thấy {len(effect_types)} hiệu ứng từ registry")
                    except Exception as e2:
                        _LOGGER.error(f"Lỗi khi lấy registry: {e2}")
                        # Không sử dụng danh sách cố định nữa
                        _LOGGER.debug("Không thể lấy danh sách hiệu ứng")
                        effect_types = []
            except Exception as e:
                _LOGGER.error(f"Lỗi khi tạo menu hiệu ứng: {e}")
                effect_types = []

            for effect_type in effect_types:
                # Skip abstract base classes and internal effects
                if effect_type.startswith('_') or effect_type == 'Effect':
                    continue

                # Add effect to menu
                _LOGGER.debug(f"Thêm hiệu ứng {effect_type} vào menu")

                # Lấy tên hiệu ứng thân thiện từ thuộc tính NAME của lớp hiệu ứng
                try:
                    # Lấy lớp hiệu ứng từ registry
                    effect_class = self.effects._cls.registry().get(effect_type)
                    # Lấy tên hiệu ứng từ thuộc tính NAME
                    if effect_class and hasattr(effect_class, 'NAME'):
                        display_name = effect_class.NAME
                        _LOGGER.debug(f"Tên hiển thị cho {effect_type}: {display_name}")
                    else:
                        display_name = effect_type
                        _LOGGER.debug(f"Không tìm thấy tên hiển thị cho {effect_type}, sử dụng tên mặc định")
                except Exception as e:
                    _LOGGER.error(f"Lỗi khi lấy tên hiển thị cho {effect_type}: {e}")
                    display_name = effect_type

                # Sử dụng một hàm đơn giản với tham số cố định
                # Tạo một bản sao của effect_type để sử dụng trong hàm
                current_effect = effect_type

                def make_handler(effect_name):
                    def handler(*args, **kwargs):
                        _LOGGER.debug(f"Menu handler gọi apply_effect_to_all('{effect_name}')")
                        self.apply_effect_to_all(effect_name)
                    return handler

                effects_items.append(
                    MenuItem(display_name, make_handler(current_effect))
                )

            # Nhóm các hiệu ứng theo danh mục
            _LOGGER.debug("Bắt đầu nhóm hiệu ứng theo danh mục")

            # Dictionary để lưu trữ các hiệu ứng theo danh mục
            categories = {}

            # Sắp xếp lại danh sách effects_items
            new_effects_items = []

            # Duyệt qua tất cả các hiệu ứng đã tạo
            for item in effects_items:
                effect_name = item.text
                # Tìm hiệu ứng trong registry
                for effect_type, effect_class in self.effects._cls.registry().items():
                    # Kiểm tra xem hiệu ứng có thuộc tính NAME khớp với tên hiển thị không
                    if hasattr(effect_class, 'NAME') and effect_class.NAME == effect_name:
                        # Lấy danh mục của hiệu ứng
                        category = "Khác"
                        if hasattr(effect_class, 'CATEGORY'):
                            category = effect_class.CATEGORY

                        # Thêm hiệu ứng vào danh mục tương ứng
                        if category not in categories:
                            categories[category] = []

                        categories[category].append(item)
                        break
                else:
                    # Nếu không tìm thấy hiệu ứng trong registry, thêm vào danh mục "Khác"
                    if "Khác" not in categories:
                        categories["Khác"] = []
                    categories["Khác"].append(item)

            # Bản dịch tiếng Anh cho các danh mục
            category_translations = {
                "1. Hiệu ứng màu": "1. Hiệu ứng màu | Color Effects",
                "2. Hiệu ứng nháy theo nhạc": "2. Nháy nhạc | Music Effects",
            }

            # Sắp xếp các danh mục theo tên
            sorted_categories = sorted(categories.keys())

            # Tạo menu con cho từng danh mục
            for category in sorted_categories:
                # Sắp xếp các hiệu ứng trong danh mục theo tên
                category_items = sorted(categories[category], key=lambda item: item.text)

                # Thêm thông tin hiệu ứng đang chọn
                if hasattr(self, 'current_effect') and self.current_effect:
                    for i, item in enumerate(category_items):
                        # Kiểm tra xem hiệu ứng này có phải là hiệu ứng đang chọn không
                        for effect_type, effect_class in self.effects._cls.registry().items():
                            if (hasattr(effect_class, 'NAME') and
                                effect_class.NAME == item.text and
                                effect_type == self.current_effect):
                                # Đánh dấu hiệu ứng đang chọn
                                # Sử dụng _action thay vì action
                                if hasattr(item, '_action'):
                                    category_items[i] = MenuItem(f"✓ {item.text}", item._action)
                                break

                # Tạo menu con cho danh mục
                category_menu = Menu(*category_items)

                # Thêm menu con vào danh sách hiệu ứng với tên đã dịch
                display_category = category_translations.get(category, category)

                # Kiểm tra xem có hiệu ứng nào trong danh mục này đang được chọn không
                if hasattr(self, 'current_effect') and self.current_effect:
                    for effect_type, effect_class in self.effects._cls.registry().items():
                        if (effect_type == self.current_effect and
                            hasattr(effect_class, 'CATEGORY') and
                            effect_class.CATEGORY == category):
                            # Thêm tên hiệu ứng đang chọn vào tên danh mục
                            if hasattr(effect_class, 'NAME'):
                                display_category = f"{display_category} :   {effect_class.NAME}"
                            else:
                                display_category = f"{display_category} :   {effect_type}"
                            break

                new_effects_items.append(MenuItem(display_category, category_menu))

            # Thay thế danh sách hiệu ứng cũ bằng danh sách mới đã nhóm
            effects_items = new_effects_items

            _LOGGER.debug(f"Đã tạo menu với {len(effects_items)} danh mục hiệu ứng")

        # Tạo danh sách các mục cho menu chính
        main_menu_items = [
            MenuItem(lambda text: toggle_text, self.toggle_startup_mode),
            Menu.SEPARATOR,
            MenuItem(lambda text: led_toggle_text, self.toggle_led_state),
            MenuItem(f"Độ sáng | Brightness :   {current_brightness}%", brightness_submenu),
            Menu.SEPARATOR
        ]

        # Thêm các danh mục hiệu ứng vào menu chính
        for effect_category_item in effects_items:
            main_menu_items.append(effect_category_item)

        # Thêm các mục còn lại
        main_menu_items.extend([
            MenuItem("3. Theo màu màn hình | Screen capture", self.stop_aw),
            Menu.SEPARATOR,
            MenuItem("Cài đặt | Setting", self.open_ui, default=True),
            MenuItem("Nâng cao | Advanced", advanced_submenu),
            Menu.SEPARATOR,
            MenuItem("RAINBOW MUSIC LED", Menu(
                MenuItem("Hướng dẫn | Guide", lambda: webbrowser.open("https://rainbowmusicled.com/huong-dan")),
                MenuItem("Hỗ trợ | Support", lambda: webbrowser.open("https://rainbowmusicled.com/ho-tro")),
                MenuItem("Bảo hành | Warranty", lambda: webbrowser.open("https://rainbowmusicled.com/bao-hanh")),
                MenuItem("Cửa hàng | Shop", lambda: webbrowser.open("https://rainbowmusicled.com")),
            )),
            Menu.SEPARATOR,
            MenuItem("Thoát | Quit", lambda: self.stop(0)),
        ])

        # Tạo menu chính
        self.icon.menu = Menu(*main_menu_items)

    # Compatibility methods for backward compatibility
    def setup_icon_menu_aw(self):
        """Legacy method, redirects to toggle_startup_mode"""
        self.toggle_startup_mode()

    def setup_icon_menu_wls(self):
        """Legacy method, redirects to toggle_startup_mode"""
        self.toggle_startup_mode()

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

        # Áp dụng hiệu ứng đã lưu (nếu có)
        if hasattr(self, 'current_effect') and self.current_effect:
            try:
                _LOGGER.debug(f"Áp dụng hiệu ứng đã lưu: {self.current_effect}")
                self.apply_effect_to_all(self.current_effect)
            except Exception as e:
                _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng đã lưu: {e}")
                # Nếu có lỗi, đặt lại hiệu ứng hiện tại
                self.current_effect = None

        # Cập nhật menu sau khi effects đã được khởi tạo
        if self.icon:
            _LOGGER.debug("Cập nhật menu sau khi effects đã được khởi tạo")
            self.setup_icon_menu()
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
