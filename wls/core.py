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
        self.current_effect = None  # Hiệu ứng đang được chọn sẽ được cập nhật sau - sẽ được cập nhật sau khi tải cấu hình

        if clear_config:
            _LOGGER.warning("Clearing WiFi Led Studio config.")
            create_backup(config_dir, "DELETE")

        self.config = load_config(config_dir)

        # Khởi tạo trạng thái LED dựa trên device_states trong cấu hình
        self.led_active = False
        if "device_states" in self.config:
            self.led_active = any(self.config["device_states"].values())
        _LOGGER.debug(f"Đã khởi tạo trạng thái LED: {'Bật' if self.led_active else 'Tắt'}")

        # Đọc lựa chọn thiết bị từ cấu hình
        if "selected_device" in self.config:
            self._selected_device = self.config["selected_device"]
            _LOGGER.debug(f"Đã đọc lựa chọn thiết bị từ cấu hình: {self._selected_device}")

        if clear_effects:
            _LOGGER.warning("Clearing active effects.")
            remove_virtuals_active_effects(self.config)

        # Không còn sử dụng current_effect từ cấu hình, thay vào đó sử dụng device_effects
        # Hiệu ứng chung sẽ được xác định từ device_effects khi khởi động
        self.config["wls_presets"] = wls_presets
        self.host = host if host else self.config["host"]
        self.port = port if port else self.config["port"]
        self.port_s = port_s if port_s else self.config["port_s"]

        # Không còn khôi phục hiệu ứng từ current_effect trong cấu hình
        # Hiệu ứng sẽ được xác định từ device_effects khi khởi động
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

        # Hiển thị menu "Đang khởi động..." trước khi khởi tạo các thành phần
        if self.icon:
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

    def get_led_devices_menu_title(self, led_devices_items):
        """
        Lấy tiêu đề menu cho mục Danh sách đèn.

        Args:
            led_devices_items: Danh sách các mục menu thiết bị LED

        Returns:
            Tiêu đề menu không hiển thị thiết bị được chọn
        """
        return "Đèn cần chỉnh | Instance to control :"

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
            try:
                # Sử dụng ctypes để hiển thị hộp thoại MessageBox của Windows
                # MB_YESNO | MB_ICONWARNING = 0x00000034
                result = ctypes.windll.user32.MessageBoxW(
                    0,
                    "Bạn có chắc chắn muốn khôi phục về mặc định không nếu mọi cài đặt trước đây của bạn sẽ bị xoá?",
                    "Xác nhận",
                    0x00000034
                )

                # Nếu người dùng nhấn Yes (IDYES = 6)
                if result == 6:
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
                        # Hiển thị lỗi bằng MessageBox thay vì messagebox của tkinter
                        ctypes.windll.user32.MessageBoxW(
                            0,
                            f"Không thể chạy chương trình: {e}",
                            "Lỗi",
                            0x00000010  # MB_ICONERROR
                        )
                        _LOGGER.error(f"Lỗi khi khôi phục mặc định: {e}")
            except Exception as e:
                _LOGGER.error(f"Lỗi khi hiển thị hộp thoại xác nhận: {e}")
        elif sys.platform == "darwin":
            try:
                # Sử dụng AppleScript để hiển thị hộp thoại xác nhận trên macOS
                script = '''
                tell application "System Events"
                    display dialog "Bạn có chắc chắn muốn khôi phục về mặc định không nếu mọi cài đặt trước đây của bạn sẽ bị xoá?" buttons {"Không", "Có"} default button "Không" with icon caution with title "Xác nhận"
                    set the button_pressed to the button returned of the result
                    if the button_pressed is "Có" then
                        return "yes"
                    else
                        return "no"
                    end if
                end tell
                '''

                # Chạy AppleScript và lấy kết quả
                proc = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE)
                result = proc.communicate()[0].decode('utf-8').strip()

                # Nếu người dùng nhấn Có
                if result == "yes":
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
            except Exception as e:
                _LOGGER.error(f"Lỗi khi khôi phục mặc định trên macOS: {e}")
        else:
            _LOGGER.error(f"Khôi phục mặc định không được hỗ trợ trên nền tảng: {sys.platform}")

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
            menu_text = "Mở rộng màn khi khởi động máy | Enable autostart Screen capture"
        else:
            # Switch to AW mode
            self.delete_wls_key()
            self.add_aw_key()
            menu_text = "Nháy nhạc khi khởi động máy | Enable autostart Music effect"

        # Update menu
        self.setup_icon_menu(toggle_text=menu_text)

    def toggle_led_state(self):
        """
        Toggle LED state between on and off.
        When turning off, it clears all effects (like the stop/clear button in UI).
        When turning on, it resumes normal operation.
        Based on the selection in the LED Devices menu.
        """
        # Check if a specific device is selected
        if hasattr(self, '_selected_device'):
            device_id = self._selected_device
            _LOGGER.debug(f"Chuyển đổi trạng thái đèn cho thiết bị: {device_id}")

            # Find virtuals associated with this device
            device_virtuals = []
            for virtual_id, virtual in self.virtuals._virtuals.items():
                if hasattr(virtual, 'is_device') and virtual.is_device == device_id:
                    device_virtuals.append(virtual)

            if device_virtuals:
                if self.led_active:
                    # Turn off LEDs for this device by clearing effects
                    for virtual in device_virtuals:
                        virtual.clear_effect()

                        # Update config to remove effect for this virtual
                        for i, virtual_config in enumerate(self.config["virtuals"]):
                            if virtual_config["id"] == virtual.id:
                                if "effect" in virtual_config:
                                    del virtual_config["effect"]
                                self.config["virtuals"][i] = virtual_config

                    # Lưu trạng thái tắt của thiết bị vào cấu hình
                    if "device_states" not in self.config:
                        self.config["device_states"] = {}
                    self.config["device_states"][str(device_id)] = False

                    # Lưu cấu hình
                    from wls.config import save_config
                    save_config(self.config, self.config_dir)

                    _LOGGER.debug(f"Đã xóa hiệu ứng và tắt đèn LED cho thiết bị {device_id}")
                else:
                    # Turn on LEDs for this device by applying the last used effect
                    try:
                        # Kiểm tra xem có hiệu ứng đã lưu cho thiết bị này không
                        effect_to_apply = self.current_effect
                        if "device_effects" in self.config and str(device_id) in self.config["device_effects"]:
                            effect_to_apply = self.config["device_effects"][str(device_id)]
                            _LOGGER.debug(f"Áp dụng hiệu ứng đã lưu cho thiết bị {device_id}: {effect_to_apply}")
                        else:
                            _LOGGER.debug(f"Áp dụng hiệu ứng mặc định: {effect_to_apply} cho thiết bị {device_id}")

                        self.apply_effect_to_device(effect_to_apply, device_id)

                        # Lưu trạng thái bật của thiết bị vào cấu hình
                        if "device_states" not in self.config:
                            self.config["device_states"] = {}
                        self.config["device_states"][str(device_id)] = True

                        # Lưu cấu hình
                        from wls.config import save_config
                        save_config(self.config, self.config_dir)

                        _LOGGER.debug(f"Đã bật đèn LED cho thiết bị {device_id} với hiệu ứng: {effect_to_apply}")
                    except Exception as e:
                        _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng đã lưu cho thiết bị {device_id}: {e}")
            else:
                _LOGGER.debug(f"Không tìm thấy thiết bị ảo nào liên kết với thiết bị {device_id}, bỏ qua")
                # Xóa thiết bị đã chọn vì nó không tồn tại
                delattr(self, '_selected_device')
        else:
            # No specific device selected, toggle all LEDs
            if self.led_active:
                # Turn off all LEDs by clearing all effects
                for virtual_id, virtual in self.virtuals._virtuals.items():
                    virtual.clear_effect()

                # Update config to remove effects
                remove_virtuals_active_effects(self.config)

                # Lưu trạng thái tắt của tất cả thiết bị vào cấu hình
                if "device_states" not in self.config:
                    self.config["device_states"] = {}

                # Đặt trạng thái tắt cho tất cả thiết bị
                for virtual_id, virtual in self.virtuals._virtuals.items():
                    if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                        self.config["device_states"][str(virtual.is_device)] = False

                # Lưu cấu hình
                from wls.config import save_config
                save_config(self.config, self.config_dir)

                _LOGGER.debug("Đã xóa hiệu ứng và tắt tất cả đèn LED")
            else:
                # Turn on all LEDs by applying the last used effect
                try:
                    # Kiểm tra xem có hiệu ứng đã lưu cho từng thiết bị không
                    if "device_effects" in self.config and self.config["device_effects"]:
                        _LOGGER.debug("Áp dụng hiệu ứng đã lưu cho từng thiết bị")
                        for device_id, effect_type in self.config["device_effects"].items():
                            _LOGGER.debug(f"Áp dụng hiệu ứng đã lưu {effect_type} cho thiết bị {device_id}")
                            self.apply_effect_to_device(effect_type, device_id)
                    else:
                        # Nếu không có hiệu ứng đã lưu cho từng thiết bị, áp dụng hiệu ứng chung
                        _LOGGER.debug(f"Áp dụng hiệu ứng chung đã lưu: {self.current_effect}")
                        self.apply_effect_to_all(self.current_effect)

                    # Lưu trạng thái bật của tất cả thiết bị vào cấu hình
                    if "device_states" not in self.config:
                        self.config["device_states"] = {}

                    # Đặt trạng thái bật cho tất cả thiết bị
                    for virtual_id, virtual in self.virtuals._virtuals.items():
                        if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                            self.config["device_states"][str(virtual.is_device)] = True

                    # Lưu cấu hình
                    from wls.config import save_config
                    save_config(self.config, self.config_dir)

                    _LOGGER.debug(f"Đã bật tất cả đèn LED với hiệu ứng: {self.current_effect}")
                except Exception as e:
                    _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng đã lưu: {e}")

        # Update menu to reflect new state
        self.setup_icon_menu()

    def set_brightness(self, brightness_value):
        """
        Set brightness for selected device or globally.

        Args:
            brightness_value (float): Brightness value between 0.0 and 1.0
        """
        # Ensure brightness is within valid range
        brightness_value = max(0.0, min(brightness_value, 1.0))

        # Check if a specific device is selected
        if hasattr(self, '_selected_device'):
            device_id = self._selected_device
            _LOGGER.debug(f"Đặt độ sáng cho thiết bị cụ thể: {device_id}")

            # Find virtuals associated with this device
            device_virtuals = []
            for virtual_id, virtual in self.virtuals._virtuals.items():
                if hasattr(virtual, 'is_device') and virtual.is_device == device_id:
                    device_virtuals.append(virtual_id)

            if device_virtuals:
                # Update max_brightness for each virtual associated with this device
                for virtual_id in device_virtuals:
                    # Find the virtual in the config
                    for i, virtual_config in enumerate(self.config["virtuals"]):
                        if virtual_config["id"] == virtual_id:
                            # Ensure config has the necessary structure
                            if "config" not in virtual_config:
                                virtual_config["config"] = {}

                            # Update max_brightness
                            virtual_config["config"]["max_brightness"] = brightness_value
                            self.config["virtuals"][i] = virtual_config
                            _LOGGER.debug(f"Đã cập nhật độ sáng cho thiết bị ảo {virtual_id} thành {int(brightness_value * 100)}%")

                            # Apply the brightness to the virtual
                            virtual = self.virtuals.get(virtual_id)
                            if virtual and hasattr(virtual, 'set_brightness'):
                                virtual.set_brightness(brightness_value)

                _LOGGER.info(f"Đã đặt độ sáng cho thiết bị {device_id} thành {int(brightness_value * 100)}%")
            else:
                _LOGGER.debug(f"Không tìm thấy thiết bị ảo nào liên kết với thiết bị {device_id}, bỏ qua")
                # Nếu thiết bị này đang được chọn, xóa nó
                if hasattr(self, '_selected_device') and self._selected_device == device_id:
                    delattr(self, '_selected_device')
        else:
            # Update max_brightness for all devices
            _LOGGER.info(f"Đặt độ sáng cho tất cả thiết bị thành {int(brightness_value * 100)}%")

            # Update max_brightness for all virtuals
            for virtual_id, virtual in self.virtuals._virtuals.items():
                # Update the virtual object
                if hasattr(virtual, '_config'):
                    virtual._config["max_brightness"] = brightness_value

                # Update the config
                for i, virtual_config in enumerate(self.config["virtuals"]):
                    if virtual_config["id"] == virtual_id:
                        if "config" not in virtual_config:
                            virtual_config["config"] = {}
                        virtual_config["config"]["max_brightness"] = brightness_value
                        self.config["virtuals"][i] = virtual_config

        # Save config
        from wls.config import save_config
        save_config(self.config, self.config_dir)

        # Update menu to reflect new state
        if self.icon:
            try:
                self.setup_icon_menu()
                _LOGGER.debug(f"Đã cập nhật menu sau khi thay đổi độ sáng thành {int(brightness_value * 100)}%")
            except Exception as e:
                _LOGGER.error(f"Lỗi khi cập nhật menu độ sáng: {e}")

    # Phương thức set_global_brightness đã được loại bỏ vì không còn cần thiết

    def _normalize_effect_type(self, effect_type):
        """
        Normalize effect type by checking registry and finding case-insensitive matches.

        Args:
            effect_type (str): The effect type to normalize

        Returns:
            str: Normalized effect type that exists in registry
        """
        # Kiểm tra xem effect_type có trong registry không
        registry = self.effects._cls.registry()

        # Nếu effect_type không có trong registry, thử tìm kiếm không phân biệt chữ hoa/thường
        if effect_type not in registry:
            for reg_effect in registry.keys():
                if effect_type.lower() == reg_effect.lower():
                    effect_type = reg_effect
                    _LOGGER.debug(f"Đã tìm thấy hiệu ứng {effect_type} trong registry")
                    break

        return effect_type

    def _apply_effect_to_virtuals(self, effect_type, virtuals, device_id=None):
        """
        Apply an effect to a list of virtual devices.

        Args:
            effect_type (str): The effect type to apply
            virtuals (list): List of virtual devices to apply the effect to
            device_id (str, optional): The device ID if applying to a specific device

        Returns:
            bool: True if successful, False otherwise
        """
        success = False

        for virtual in virtuals:
            try:
                # Tạo hiệu ứng mới
                effect = self.effects.create(
                    type=effect_type,
                    config={},
                    wls=self,
                )

                # Đặt hiệu ứng cho thiết bị ảo
                virtual.set_effect(effect)

                # Cập nhật cấu hình
                from wls.virtuals import update_effect_config
                update_effect_config(self.config, virtual.id, effect)

                _LOGGER.debug(f"Đã áp dụng hiệu ứng {effect_type} cho thiết bị ảo {virtual.id}")
                success = True
            except Exception as e:
                _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng {effect_type} cho thiết bị ảo {virtual.id}: {e}")
                import traceback
                _LOGGER.error(traceback.format_exc())

        return success

    def apply_effect_to_device(self, effect_type, device_id):
        """
        Apply an effect to a specific device.

        Args:
            effect_type (str): The effect type to apply
            device_id (str): The ID of the device to apply the effect to
        """
        _LOGGER.debug(f"Bắt đầu áp dụng hiệu ứng {effect_type} cho thiết bị {device_id}")
        try:
            # Chuẩn hóa effect_type
            effect_type = self._normalize_effect_type(effect_type)

            # Tìm các thiết bị ảo liên quan đến thiết bị này
            device_virtuals = []
            for virtual_id, virtual in self.virtuals._virtuals.items():
                # Kiểm tra xem virtual có liên kết với device_id không
                if hasattr(virtual, 'is_device') and virtual.is_device == device_id:
                    device_virtuals.append(virtual)
                    _LOGGER.debug(f"Tìm thấy thiết bị ảo {virtual_id} liên kết với thiết bị {device_id}")

            if not device_virtuals:
                _LOGGER.debug(f"Không tìm thấy thiết bị ảo nào liên kết với thiết bị {device_id}, bỏ qua")
                # Nếu thiết bị này đang được chọn, xóa nó
                if hasattr(self, '_selected_device') and self._selected_device == device_id:
                    delattr(self, '_selected_device')
                return

            # Áp dụng hiệu ứng cho các thiết bị ảo liên quan
            success = self._apply_effect_to_virtuals(effect_type, device_virtuals, device_id)

            if not success:
                return

            # Lưu hiệu ứng hiện tại cho thiết bị cụ thể
            self.current_effect = effect_type

            # Lưu hiệu ứng hiện tại của thiết bị vào cấu hình
            if "device_effects" not in self.config:
                self.config["device_effects"] = {}
            self.config["device_effects"][str(device_id)] = effect_type
            _LOGGER.debug(f"Đã lưu hiệu ứng {effect_type} cho thiết bị {device_id} vào cấu hình")

            _LOGGER.info(f"Đã áp dụng hiệu ứng {effect_type} cho thiết bị {device_id}")

            # Cập nhật trạng thái LED thành bật
            self.led_active = True
            _LOGGER.debug("Đã cập nhật trạng thái LED thành bật")

            # Lưu cấu hình sau khi đã cập nhật device_effects
            from wls.config import save_config
            save_config(self.config, self.config_dir)
            _LOGGER.debug(f"Đã lưu cấu hình với hiệu ứng {effect_type} cho thiết bị {device_id}")

            # Cập nhật menu
            if self.icon:
                try:
                    self.setup_icon_menu()
                    _LOGGER.debug(f"Đã cập nhật menu sau khi chọn hiệu ứng {effect_type} cho thiết bị {device_id}")
                except Exception as e:
                    _LOGGER.error(f"Lỗi khi cập nhật menu: {e}")

        except Exception as e:
            _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng {effect_type} cho thiết bị {device_id}: {e}")
            import traceback
            _LOGGER.error(traceback.format_exc())

    def apply_effect_to_all(self, effect_type):
        """
        Apply an effect to all virtual devices.

        Args:
            effect_type (str): The effect type to apply
        """
        _LOGGER.debug(f"Bắt đầu áp dụng hiệu ứng {effect_type} (type: {type(effect_type)}) cho tất cả thiết bị ảo")
        try:
            # Chuẩn hóa effect_type
            effect_type = self._normalize_effect_type(effect_type)
            _LOGGER.debug(f"Registry có {len(self.effects._cls.registry())} hiệu ứng")

            # Đảm bảo device_effects tồn tại trong cấu hình
            if "device_effects" not in self.config:
                self.config["device_effects"] = {}

            # Áp dụng hiệu ứng cho tất cả thiết bị ảo
            success = self._apply_effect_to_virtuals(effect_type, list(self.virtuals.values()))

            if not success:
                return

            # Lưu hiệu ứng cho từng thiết bị thực
            for virtual in self.virtuals.values():
                if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                    device_id = virtual.is_device
                    self.config["device_effects"][str(device_id)] = effect_type
                    _LOGGER.debug(f"Đã lưu hiệu ứng {effect_type} cho thiết bị {device_id} vào cấu hình")

            # Lưu hiệu ứng hiện tại
            self.current_effect = effect_type
            _LOGGER.info(f"Đã áp dụng hiệu ứng {effect_type} cho tất cả thiết bị ảo")

            # Cập nhật trạng thái LED thành bật
            self.led_active = True
            _LOGGER.debug("Đã cập nhật trạng thái LED thành bật")

            # Lưu cấu hình sau khi đã cập nhật device_effects
            from wls.config import save_config
            save_config(self.config, self.config_dir)
            _LOGGER.debug(f"Đã lưu cấu hình với hiệu ứng {effect_type} cho tất cả thiết bị")

            # Chỉ cập nhật menu một lần sau khi đã áp dụng hiệu ứng cho tất cả thiết bị
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



    # Helper methods for menu generation
    def get_selected_device(self):
        """
        Get the currently selected device ID or None if all devices are selected.

        Returns:
            str or None: The selected device ID or None if all devices are selected
        """
        return getattr(self, '_selected_device', None)

    def get_current_effect(self, device_id=None):
        """
        Get the current effect for a device or the global effect.

        Args:
            device_id (str, optional): The device ID to get the effect for

        Returns:
            str: The current effect type
        """
        # If a specific device is provided, check its effect
        if device_id and "device_effects" in self.config and str(device_id) in self.config["device_effects"]:
            return self.config["device_effects"][str(device_id)]

        # If no device is provided but a device is selected, check its effect
        selected_device = self.get_selected_device()
        if selected_device and "device_effects" in self.config and str(selected_device) in self.config["device_effects"]:
            return self.config["device_effects"][str(selected_device)]

        # If no device is selected, try to get the effect of the first device
        if not selected_device and "device_effects" in self.config:
            # Get the first device
            first_device = self._get_first_device()
            if first_device and str(first_device.id) in self.config["device_effects"]:
                return self.config["device_effects"][str(first_device.id)]

        # Fall back to the global current effect
        return getattr(self, 'current_effect', None)

    def get_current_brightness(self, device_id=None):
        """
        Get the current brightness for a device or the global brightness.

        Args:
            device_id (str, optional): The device ID to get the brightness for

        Returns:
            int: The current brightness percentage (0-100)
        """
        # Default brightness
        default_brightness = 100

        # If no specific device is provided, use the selected device
        if not device_id:
            device_id = self.get_selected_device()

        # If a device is specified, find its virtual and get brightness
        if device_id:
            device_virtual = self._find_virtual_for_device(device_id)
            if device_virtual:
                for virtual_config in self.config.get("virtuals", []):
                    if virtual_config["id"] == device_virtual:
                        if "config" in virtual_config and "max_brightness" in virtual_config["config"]:
                            return int(virtual_config["config"]["max_brightness"] * 100)
        else:
            # If no device is selected, get brightness from the first device
            first_device_virtual = self._find_virtual_for_first_device()
            if first_device_virtual:
                for virtual_config in self.config.get("virtuals", []):
                    if virtual_config["id"] == first_device_virtual:
                        if "config" in virtual_config and "max_brightness" in virtual_config["config"]:
                            return int(virtual_config["config"]["max_brightness"] * 100)

        return default_brightness

    def _find_virtual_for_device(self, device_id):
        """
        Find the virtual ID associated with a device.

        Args:
            device_id (str): The device ID

        Returns:
            str or None: The virtual ID or None if not found
        """
        for virtual_id, virtual in self.virtuals._virtuals.items():
            if hasattr(virtual, 'is_device') and virtual.is_device == device_id:
                return virtual_id
        return None

    def _find_virtual_for_first_device(self):
        """
        Find the virtual ID associated with the first device.

        Returns:
            str or None: The virtual ID or None if not found
        """
        for virtual_id, virtual in self.virtuals._virtuals.items():
            if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                return virtual_id
        return None

    def _get_first_device(self):
        """
        Get the first device from the list of devices.

        Returns:
            object or None: The first device or None if no devices are found
        """
        devices = self._get_all_devices()
        return devices[0] if devices else None

    def _get_all_devices(self):
        """
        Get all devices from various sources.

        Returns:
            list: List of device objects
        """
        devices = []
        device_ids_added = set()

        # Helper class for device info
        class DeviceInfo:
            def __init__(self, device_id, name=None):
                self.id = device_id
                self.name = name or f"Device {device_id}"

        # 1. Try to get from self.devices
        if hasattr(self, 'devices') and self.devices:
            for device in self.devices.values():
                if device.id not in device_ids_added:
                    devices.append(device)
                    device_ids_added.add(device.id)

        # 2. Try to get from self.virtuals
        if hasattr(self, 'virtuals') and hasattr(self.virtuals, '_virtuals') and self.virtuals._virtuals:
            for virtual_id, virtual in self.virtuals._virtuals.items():
                if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                    device_id = virtual.is_device
                    if device_id not in device_ids_added:
                        # Find device name from virtuals config
                        device_name = f"Device {device_id}"

                        # Look in virtuals config
                        if "virtuals" in self.config:
                            for virtual_config in self.config["virtuals"]:
                                if virtual_config.get("id") == virtual_id:
                                    if "config" in virtual_config and "name" in virtual_config["config"]:
                                        device_name = virtual_config["config"]["name"]
                                        break

                        # If not found in virtuals, try devices
                        if device_name == f"Device {device_id}" and "devices" in self.config:
                            for device_config in self.config["devices"]:
                                if device_config.get("id") == device_id and "name" in device_config:
                                    device_name = device_config["name"]
                                    break

                        devices.append(DeviceInfo(device_id, device_name))
                        device_ids_added.add(device_id)

        # 3. Try to get from config if still no devices
        if not devices and "devices" in self.config:
            for device_config in self.config["devices"]:
                device_id = device_config.get("id")
                if device_id is not None and device_id not in device_ids_added:
                    # Find device name from virtuals config first
                    device_name = None

                    # Look in virtuals config
                    if "virtuals" in self.config:
                        for virtual_config in self.config["virtuals"]:
                            if "is_device" in virtual_config and virtual_config["is_device"] == device_id:
                                if "config" in virtual_config and "name" in virtual_config["config"]:
                                    device_name = virtual_config["config"]["name"]
                                    break

                    # If not found in virtuals, use name from devices
                    if not device_name:
                        device_name = device_config.get("name", f"Device {device_id}")

                    devices.append(DeviceInfo(device_id, device_name))
                    device_ids_added.add(device_id)

        return devices

    def is_device_active(self, device_id=None):
        """
        Check if a device is active (turned on).

        Args:
            device_id (str, optional): The device ID to check

        Returns:
            bool: True if the device is active, False otherwise
        """
        # If no specific device is provided, use the selected device
        if not device_id:
            device_id = self.get_selected_device()

        # If a device is specified, check its state
        if device_id:
            if "device_states" in self.config and str(device_id) in self.config["device_states"]:
                return self.config["device_states"][str(device_id)]
            return True  # Default to active if not specified
        else:
            # If no device is selected, check if any device is active
            if "device_states" in self.config:
                return any(self.config["device_states"].values())
            return True  # Default to active if not specified

    def generate_brightness_submenu(self):
        """
        Generate the brightness submenu with checkmarks for the current brightness.

        Returns:
            Menu: The brightness submenu
        """
        current_brightness = self.get_current_brightness()

        # Create brightness items with checkmarks
        brightness_items = []
        for brightness in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            brightness_text = f"{brightness}%"
            if brightness == current_brightness:
                brightness_text = f"✓ {brightness_text}"

            # Create a closure to preserve the brightness value
            def make_brightness_handler(value):
                return lambda: self.set_brightness(value/100)

            brightness_items.append(
                MenuItem(brightness_text, make_brightness_handler(brightness))
            )

        return Menu(*brightness_items)

    def generate_effects_submenu(self):
        """
        Generate the effects submenu grouped by category with checkmarks for the current effect.
        Optimized version to reduce processing time with many devices.

        Returns:
            list: List of effect category menu items
        """
        if not hasattr(self, 'effects') or self.effects is None:
            _LOGGER.debug("self.effects not initialized, skipping effects menu")
            return []

        try:
            # Use cached registry if available to avoid repeated lookups
            if not hasattr(self, '_effects_registry_cache'):
                try:
                    self._effects_registry_cache = self.effects._cls.registry()
                    self._effects_types_cache = self.effects.types()
                except Exception as e:
                    _LOGGER.error(f"Error initializing effects cache: {e}")
                    try:
                        self._effects_registry_cache = self.effects._cls.registry()
                        self._effects_types_cache = list(self._effects_registry_cache.keys())
                    except Exception as e2:
                        _LOGGER.error(f"Error getting registry: {e2}")
                        return []

            # Get current effect once
            current_effect = self.get_current_effect()

            # Pre-process effect classes to avoid repeated lookups
            effect_info = {}
            categories = {}

            # First pass: collect all effect information
            for effect_type in self._effects_types_cache:
                # Skip abstract base classes and internal effects
                if effect_type.startswith('_') or effect_type == 'Effect':
                    continue

                effect_class = self._effects_registry_cache.get(effect_type)
                if not effect_class:
                    continue

                # Get effect name and category
                display_name = getattr(effect_class, 'NAME', effect_type)
                category = getattr(effect_class, 'CATEGORY', "Khác")

                # Store effect info
                effect_info[effect_type] = {
                    'name': display_name,
                    'category': category,
                    'is_current': effect_type == current_effect
                }

                # Initialize category if needed
                if category not in categories:
                    categories[category] = []

            # Create menu items with handlers
            for effect_type, info in effect_info.items():
                # Create handler for this effect
                def make_handler(effect_name):
                    def handler():
                        if self.get_selected_device():
                            self.apply_effect_to_device(effect_name, self.get_selected_device())
                        else:
                            self.apply_effect_to_all(effect_name)
                    return handler

                # Create menu item
                display_text = info['name']
                if info['is_current']:
                    display_text = f"✓ {display_text}"

                menu_item = MenuItem(display_text, make_handler(effect_type))
                categories[info['category']].append(menu_item)

            # Category translations
            category_translations = {
                "1. Hiệu ứng màu": "⚬ Hiệu ứng màu | Color Effects",
                "2. Hiệu ứng nháy theo nhạc": "⚬ Nháy nhạc | Music Effects",
            }

            # Sort categories
            sorted_categories = sorted(categories.keys())

            # Create category submenus
            new_effects_items = []
            for category in sorted_categories:
                # Sort effects in category by name
                category_items = sorted(categories[category], key=lambda item: item.text.replace("✓ ", ""))

                # Create category submenu
                category_menu = Menu(*category_items)

                # Get display category name
                display_category = category_translations.get(category, category)

                # Add current effect name to category if it belongs to this category
                if current_effect:
                    current_info = effect_info.get(current_effect)
                    if current_info and current_info['category'] == category:
                        display_category = f"{display_category} :   {current_info['name']}"

                new_effects_items.append(MenuItem(display_category, category_menu))

            return new_effects_items

        except Exception as e:
            _LOGGER.error(f"Error generating effects menu: {e}")
            return []

    def generate_device_menu_items(self):
        """
        Generate the device menu items with checkmarks for the selected device.
        Optimized version to reduce processing time with many devices.

        Returns:
            list: List of device menu items
        """
        # Initialize cache time if not exists
        if not hasattr(self, '_devices_cache_time'):
            self._devices_cache_time = 0

        # Cache device list to avoid repeated calls
        if not hasattr(self, '_devices_cache') or self._devices_cache_time < time.time() - 5:
            self._devices_cache = self._get_all_devices()
            self._devices_cache_time = time.time()

        devices = self._devices_cache
        device_items = []
        selected_device = self.get_selected_device()

        # Create "All" option
        is_all_selected = not selected_device
        device_items.append(MenuItem(
            f"   {'✓ ' if is_all_selected else '    '}⛬ Tất cả | All",
            self.select_all_devices
        ))

        # Create device options - use a more efficient approach
        # Pre-sort devices to avoid sorting in the loop
        sorted_devices = sorted(devices, key=lambda d: d.name if hasattr(d, 'name') else d.id)

        # Create a reusable selector factory
        def create_device_selector_factory():
            # This closure captures the current state
            # and returns a factory function that creates selectors
            current_selected = selected_device

            def make_device_selector(dev_id):
                # This is the factory that creates a selector for a specific device
                def select_device():
                    self._selected_device = dev_id
                    self.config["selected_device"] = dev_id
                    from wls.config import save_config
                    save_config(self.config, self.config_dir)

                    # Update LED state based on selected device
                    if "device_states" in self.config and str(dev_id) in self.config["device_states"]:
                        self.led_active = self.config["device_states"][str(dev_id)]

                    self.setup_icon_menu()
                return select_device

            return make_device_selector

        # Create the selector factory once
        make_device_selector = create_device_selector_factory()

        # Create menu items for each device
        for device in sorted_devices:
            device_id = device.id
            is_selected = selected_device == device_id
            device_name = device.name if hasattr(device, 'name') else device_id

            device_items.append(MenuItem(
                f"   {'✓ ' if is_selected else '    '} ⚬ {device_name}",
                make_device_selector(device_id)
            ))

        return device_items

    def select_all_devices(self):
        """
        Select all devices and synchronize their state.
        """
        # Clear selected device
        if hasattr(self, '_selected_device'):
            delattr(self, '_selected_device')
        if "selected_device" in self.config:
            del self.config["selected_device"]

        # Get first device to sync state
        first_device = self._get_first_device()
        if first_device:
            first_device_id = str(first_device.id)

            # 1. Sync on/off state
            first_device_state = True
            if "device_states" in self.config and first_device_id in self.config["device_states"]:
                first_device_state = self.config["device_states"][first_device_id]

            # Apply first device state to all devices
            if "device_states" not in self.config:
                self.config["device_states"] = {}

            for device in self._get_all_devices():
                self.config["device_states"][str(device.id)] = first_device_state

            # 2. Sync brightness
            first_device_brightness = 1.0
            first_device_virtual = self._find_virtual_for_device(first_device.id)

            if first_device_virtual:
                for virtual_config in self.config.get("virtuals", []):
                    if virtual_config["id"] == first_device_virtual:
                        if "config" in virtual_config and "max_brightness" in virtual_config["config"]:
                            first_device_brightness = virtual_config["config"]["max_brightness"]
                            break

            # Apply brightness to all devices
            for virtual_id, virtual in self.virtuals._virtuals.items():
                # Update brightness in config
                for i, virtual_config in enumerate(self.config.get("virtuals", [])):
                    if virtual_config["id"] == virtual_id:
                        if "config" not in virtual_config:
                            virtual_config["config"] = {}
                        virtual_config["config"]["max_brightness"] = first_device_brightness
                        self.config["virtuals"][i] = virtual_config

                        # Apply brightness to virtual
                        if hasattr(virtual, 'set_brightness'):
                            virtual.set_brightness(first_device_brightness)

            # 3. Sync effect or turn off all lights
            if first_device_state:  # If first device is on
                first_device_effect = None

                # Find effect of first device
                if first_device_virtual:
                    for virtual_config in self.config.get("virtuals", []):
                        if virtual_config["id"] == first_device_virtual and "effect" in virtual_config:
                            first_device_effect = virtual_config["effect"]["type"]
                            break

                # Apply effect to all devices
                if first_device_effect:
                    for virtual in self.virtuals.values():
                        try:
                            effect = self.effects.create(
                                type=first_device_effect,
                                wls=self,
                                config={}
                            )
                            virtual.set_effect(effect)

                            # Update config
                            from wls.virtuals import update_effect_config
                            update_effect_config(self.config, virtual.id, effect)
                        except Exception as e:
                            _LOGGER.error(f"Error applying effect {first_device_effect} to virtual {virtual.id}: {e}")
            else:  # If first device is off
                # Turn off all lights by clearing effects
                for virtual in self.virtuals._virtuals.values():
                    virtual.clear_effect()

                # Update config to remove effects
                from wls.config import remove_virtuals_active_effects
                remove_virtuals_active_effects(self.config)
        else:
            # If no devices, update LED state based on all devices
            if "device_states" in self.config:
                self.led_active = any(self.config["device_states"].values())

        # Save config
        from wls.config import save_config
        save_config(self.config, self.config_dir)

        # Update menu
        self.setup_icon_menu()

    def get_led_devices_menu_title(self, led_devices_items=None):
        """
        Get the title for the LED devices menu section.

        Returns:
            str: The menu title
        """
        return "Đèn cần chỉnh | Instance to control :"

    def setup_icon_menu(self, toggle_text=None):
        """
        Setup the icon menu with the appropriate text based on current state.

        Args:
            toggle_text: Optional text override for the toggle menu item.
                        If None, it will be determined based on current state.
        """
        # Check if required components are initialized
        if not hasattr(self, 'virtuals') or not hasattr(self, 'devices'):
            # If not fully initialized, show simple menu
            if self.icon:
                self.icon.menu = Menu(
                    MenuItem("Đang khởi động...", lambda: None)
                )
            return

        # Initialize throttling mechanism
        if not hasattr(self, '_last_menu_update'):
            self._last_menu_update = 0
            self._menu_update_scheduled = False
            self._menu_lock = threading.Lock()
            self._menu_update_thread = None

        # Check if an update is already scheduled
        current_time = time.time()
        min_update_interval = 0.3  # Minimum time between updates in seconds

        # If an update was recently performed and no update is scheduled, schedule one
        if (current_time - self._last_menu_update < min_update_interval and
            not self._menu_update_scheduled):
            if self._menu_update_thread is None or not self._menu_update_thread.is_alive():
                self._menu_update_scheduled = True
                self._menu_update_thread = threading.Thread(
                    target=self._delayed_menu_update,
                    args=(toggle_text, min_update_interval - (current_time - self._last_menu_update)),
                    daemon=True
                )
                self._menu_update_thread.start()
                _LOGGER.debug("Menu update throttled - scheduled for later")
            return

        # Try to acquire lock with timeout to avoid deadlock
        if not self._menu_lock.acquire(timeout=1.0):
            _LOGGER.warning("Cannot update menu - could not acquire lock after 1 second")
            return

        try:
            # Update timestamp
            self._last_menu_update = time.time()
            self._menu_update_scheduled = False

            # Determine toggle text based on current state
            if toggle_text is None:
                if self.check_rmlapp_run_key():
                    toggle_text = "Nháy nhạc khi khởi động máy | Enable autostart Music effect"
                else:
                    toggle_text = "Mở rộng màn khi khởi động máy | Enable autostart Screen capture"

            # Determine LED state based on selected device
            device_active = self.is_device_active()

            # Update led_active variable
            self.led_active = device_active

            # Set LED toggle text
            led_toggle_text = "Tắt đèn | Suspend" if device_active else "Bật đèn | Resume"

            # Log current LED state
            _LOGGER.debug(f"Current LED state: {'On' if device_active else 'Off'}")

            # Create advanced submenu (static)
            advanced_submenu = Menu(
                MenuItem("Khởi động lại | Restart", self.restart_wls),
                MenuItem("Khôi phục mặc định | Restore default", self.restore),
            )

            # Create brightness submenu
            brightness_submenu = self.generate_brightness_submenu()
            current_brightness = self.get_current_brightness()

            # Create device menu items
            device_items = self.generate_device_menu_items()

            # Create effects submenu - this is the most expensive operation
            # Only regenerate if necessary (first time or after effect change)
            if not hasattr(self, '_cached_effects_items') or self._should_regenerate_effects_menu():
                effects_items = self.generate_effects_submenu()
                self._cached_effects_items = effects_items
                self._last_effect_state = self.get_current_effect()
            else:
                effects_items = self._cached_effects_items

            # Create main menu
            main_menu_items = [
                MenuItem(lambda text: toggle_text, self.toggle_startup_mode),
                Menu.SEPARATOR,
                # Display "LED Devices" title
                MenuItem(self.get_led_devices_menu_title(), None),
            ]

            # Add device items to main menu
            main_menu_items.extend(device_items)

            # Add next items
            main_menu_items.extend([
                Menu.SEPARATOR,
                MenuItem(lambda text: led_toggle_text, self.toggle_led_state),
                MenuItem(f"Độ sáng | Brightness :   {current_brightness}%", brightness_submenu),
                Menu.SEPARATOR
            ])

            # Add effect categories to main menu
            for effect_category_item in effects_items:
                main_menu_items.append(effect_category_item)

            # Add remaining items
            main_menu_items.extend([
                MenuItem("⚬ Mở rộng màn | Screen capture", self.stop_aw),
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

            # Create main menu
            self.icon.menu = Menu(*main_menu_items)
        finally:
            # Always release lock
            self._menu_lock.release()

    def _delayed_menu_update(self, toggle_text, delay):
        """
        Perform a delayed menu update to avoid rapid consecutive updates.

        Args:
            toggle_text: Text to use for the toggle menu item
            delay: Time to wait before updating in seconds
        """
        try:
            time.sleep(delay)
            self.setup_icon_menu(toggle_text)
        except Exception as e:
            _LOGGER.error(f"Error in delayed menu update: {e}")
        finally:
            self._menu_update_scheduled = False

    def _should_regenerate_effects_menu(self):
        """
        Determine if the effects menu needs to be regenerated.

        Returns:
            bool: True if the menu should be regenerated, False otherwise
        """
        # Check if the current effect has changed
        current_effect = self.get_current_effect()
        if not hasattr(self, '_last_effect_state') or self._last_effect_state != current_effect:
            return True

        # Add other conditions that would require regeneration
        # For example, if effects have been added or removed

        return False

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

        # Thêm listener cho sự kiện EffectClearedEvent
        def handle_effect_cleared(event):
            _LOGGER.debug("Nhận sự kiện EffectClearedEvent - cập nhật menu sang trạng thái 'Tắt đèn'")
            if self.icon:
                # Invalidate effects cache to force regeneration
                if hasattr(self, '_cached_effects_items'):
                    delattr(self, '_cached_effects_items')
                self.setup_icon_menu()

        self.events.add_listener(
            handle_effect_cleared,
            Event.EFFECT_CLEARED,
        )

        # Thêm listener cho sự kiện EffectSetEvent
        def handle_effect_set(event):
            _LOGGER.debug(f"Nhận sự kiện EffectSetEvent - cập nhật menu sang trạng thái 'Bật đèn' với hiệu ứng {event.effect_id}")
            if self.icon:
                # Invalidate effects cache to force regeneration
                if hasattr(self, '_cached_effects_items'):
                    delattr(self, '_cached_effects_items')
                self.setup_icon_menu()

        self.events.add_listener(
            handle_effect_set,
            Event.EFFECT_SET,
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

        # Khôi phục trạng thái bật/tắt của từng đèn từ cấu hình
        if "device_states" in self.config:
            _LOGGER.debug("Khôi phục trạng thái bật/tắt của từng đèn từ cấu hình")
            device_states = self.config["device_states"]

            # Nếu có thiết bị cụ thể được chọn, chỉ áp dụng cho thiết bị đó
            if hasattr(self, '_selected_device'):
                device_id = self._selected_device

                # Kiểm tra xem thiết bị có tồn tại không
                device_exists = False
                for virtual_id, virtual in self.virtuals._virtuals.items():
                    if hasattr(virtual, 'is_device') and virtual.is_device == device_id:
                        device_exists = True
                        break

                if not device_exists:
                    _LOGGER.debug(f"Thiết bị {device_id} không tồn tại hoặc chưa được khởi tạo, bỏ qua")
                    # Xóa thiết bị đã chọn vì nó không tồn tại
                    delattr(self, '_selected_device')
                else:
                    device_state = device_states.get(str(device_id), True)  # Mặc định là bật

                    if not device_state:
                        _LOGGER.debug(f"Thiết bị {device_id} đang ở trạng thái tắt, không áp dụng hiệu ứng")
                        # Tắt đèn cho thiết bị này
                        for virtual_id, virtual in self.virtuals._virtuals.items():
                            if virtual.is_device == device_id:
                                virtual.clear_effect()
                                _LOGGER.debug(f"Đã xóa hiệu ứng cho thiết bị ảo {virtual_id} liên kết với thiết bị {device_id}")
            else:
                # Áp dụng trạng thái cho tất cả thiết bị
                for device_id, device_state in device_states.items():
                    if not device_state:  # Nếu thiết bị đang ở trạng thái tắt
                        _LOGGER.debug(f"Thiết bị {device_id} đang ở trạng thái tắt, không áp dụng hiệu ứng")
                        # Tắt đèn cho thiết bị này
                        for virtual_id, virtual in self.virtuals._virtuals.items():
                            if hasattr(virtual, 'is_device') and virtual.is_device == int(device_id):
                                virtual.clear_effect()
                                _LOGGER.debug(f"Đã xóa hiệu ứng cho thiết bị ảo {virtual_id} liên kết với thiết bị {device_id}")

        # Áp dụng hiệu ứng đã lưu (nếu có và nếu LED đang bật)
        if self.led_active:
            try:
                # Kiểm tra xem có hiệu ứng đã lưu cho từng thiết bị không
                if "device_effects" in self.config and self.config["device_effects"]:
                    _LOGGER.debug("Khôi phục hiệu ứng cho từng thiết bị từ cấu hình")

                    # Nếu có thiết bị cụ thể được chọn, chỉ áp dụng cho thiết bị đó
                    if hasattr(self, '_selected_device'):
                        device_id = self._selected_device
                        device_effect = self.config["device_effects"].get(str(device_id))

                        # Kiểm tra xem thiết bị có đang bật không
                        if "device_states" not in self.config or self.config["device_states"].get(str(device_id), True):
                            if device_effect:
                                _LOGGER.debug(f"Áp dụng hiệu ứng đã lưu {device_effect} cho thiết bị {device_id}")
                                self.apply_effect_to_device(device_effect, device_id)
                            elif hasattr(self, 'current_effect') and self.current_effect:
                                _LOGGER.debug(f"Áp dụng hiệu ứng mặc định {self.current_effect} cho thiết bị {device_id}")
                                self.apply_effect_to_device(self.current_effect, device_id)
                    else:
                        # Áp dụng hiệu ứng cho từng thiết bị dựa trên cấu hình đã lưu
                        for device_id, effect_type in self.config["device_effects"].items():
                            # Kiểm tra xem thiết bị có đang bật không
                            if "device_states" not in self.config or self.config["device_states"].get(str(device_id), True):
                                _LOGGER.debug(f"Áp dụng hiệu ứng đã lưu {effect_type} cho thiết bị {device_id}")
                                self.apply_effect_to_device(effect_type, device_id)

                # Nếu không có hiệu ứng đã lưu cho từng thiết bị, sử dụng hiệu ứng chung
                elif hasattr(self, 'current_effect') and self.current_effect:
                    _LOGGER.debug(f"Áp dụng hiệu ứng đã lưu chung: {self.current_effect}")

                    # Kiểm tra xem có thông tin chi tiết về hiệu ứng trong cấu hình không
                    has_effect_details = False
                    for virtual_cfg in self.config["virtuals"]:
                        if "effect" in virtual_cfg and virtual_cfg["effect"].get("type") == self.current_effect:
                            has_effect_details = True
                            break

                    if has_effect_details:
                        _LOGGER.debug("Sử dụng thông tin chi tiết về hiệu ứng từ cấu hình")
                        # Khôi phục hiệu ứng từ cấu hình cho từng thiết bị ảo
                        for virtual_id, virtual in self.virtuals._virtuals.items():
                            # Kiểm tra xem thiết bị này có đang ở trạng thái tắt không
                            if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                                device_id = virtual.is_device
                                if "device_states" in self.config and str(device_id) in self.config["device_states"]:
                                    if not self.config["device_states"][str(device_id)]:
                                        _LOGGER.debug(f"Bỏ qua thiết bị {device_id} vì đang ở trạng thái tắt")
                                        continue

                            virtual_cfg = next((v for v in self.config["virtuals"] if v["id"] == virtual_id), None)
                            if virtual_cfg and "effect" in virtual_cfg:
                                effect_type = virtual_cfg["effect"]["type"]
                                effect_config = virtual_cfg["effect"]["config"]
                                try:
                                    effect = self.effects.create(
                                        type=effect_type,
                                        wls=self,
                                        config=effect_config
                                    )
                                    virtual.set_effect(effect)
                                    _LOGGER.debug(f"Đã khôi phục hiệu ứng {effect_type} cho thiết bị ảo {virtual_id}")
                                except Exception as e:
                                    _LOGGER.error(f"Lỗi khi khôi phục hiệu ứng cho thiết bị ảo {virtual_id}: {e}")
                    else:
                        _LOGGER.debug("Không tìm thấy thông tin chi tiết về hiệu ứng, áp dụng hiệu ứng mặc định")
                        # Áp dụng hiệu ứng cho tất cả thiết bị không ở trạng thái tắt
                        if hasattr(self, '_selected_device'):
                            device_id = self._selected_device
                            if "device_states" not in self.config or self.config["device_states"].get(str(device_id), True):
                                self.apply_effect_to_device(self.current_effect, device_id)
                        else:
                            # Áp dụng cho tất cả thiết bị không ở trạng thái tắt
                            for virtual_id, virtual in self.virtuals._virtuals.items():
                                if hasattr(virtual, 'is_device') and virtual.is_device is not None:
                                    device_id = virtual.is_device
                                    if "device_states" not in self.config or self.config["device_states"].get(str(device_id), True):
                                        self.apply_effect_to_device(self.current_effect, device_id)
            except Exception as e:
                _LOGGER.error(f"Lỗi khi áp dụng hiệu ứng đã lưu: {e}")
                # Nếu có lỗi, đặt lại hiệu ứng hiện tại
                self.current_effect = None
        elif not self.led_active:
            _LOGGER.debug("Không áp dụng hiệu ứng vì LED đang ở trạng thái tắt")

        # Cập nhật menu sau khi effects đã được khởi tạo
        if self.icon:
            _LOGGER.debug("Cập nhật menu sau khi effects đã được khởi tạo")
            # Nếu có lựa chọn thiết bị từ cấu hình, khôi phục lại
            if "selected_device" in self.config:
                self._selected_device = self.config["selected_device"]
                _LOGGER.debug(f"Đã khôi phục lựa chọn thiết bị từ cấu hình: {self._selected_device}")
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
