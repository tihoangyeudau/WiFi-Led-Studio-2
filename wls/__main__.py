#!/usr/bin/env python
"""
Entry point for the wls controller. To run this script for development
purposes use:

    [console_scripts]
    python setup.py develop
    wls

For non-development purposes run:

    [console_scripts]
    python setup.py install
    wls

"""

import argparse
import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler

import psutil
import yappi

import wls.config as config_helpers
from wls.consts import (
    PROJECT_NAME,
    PROJECT_VERSION,
    REQUIRED_PYTHON_STRING,
    REQUIRED_PYTHON_VERSION,
)
from wls.core import WlsCore
from wls.utils import currently_frozen


def validate_python() -> None:
    """Validate the python version for when manually running"""

    if sys.version_info[:3] < REQUIRED_PYTHON_VERSION:
        print(("Python {} is required.").format(REQUIRED_PYTHON_STRING))
        sys.exit(1)


def reset_logging():
    manager = logging.root.manager
    manager.disabled = logging.NOTSET
    for logger in manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(logging.NOTSET)
            logger.propagate = True
            logger.disabled = False
            logger.filters.clear()
            handlers = logger.handlers.copy()
            for handler in handlers:
                # Copied from `logging.shutdown`.
                try:
                    handler.acquire()
                    handler.flush()
                    handler.close()
                except (OSError, ValueError):
                    pass
                finally:
                    handler.release()
                logger.removeHandler(handler)


def setup_logging(loglevel, config_dir):
    # Create a custom logging level to virtual pyupdater progress
    reset_logging()

    console_loglevel = loglevel or logging.WARNING
    console_logformat = "[%(levelname)-8s] %(name)-30s : %(message)s"

    file_loglevel = logging.INFO
    file_logformat = "%(asctime)-8s %(name)-30s %(levelname)-8s %(message)s"

    root_logger = logging.getLogger()

    file_handler = RotatingFileHandler(
        config_helpers.get_log_file_location(config_dir),
        mode="a",  # append
        maxBytes=0.5 * 1000 * 1000,  # 512kB
        encoding="utf8",
        backupCount=5,  # once it hits 2.5MB total, start removing logs.
    )
    file_handler.setLevel(file_loglevel)  # set loglevel
    file_formatter = logging.Formatter(file_logformat)
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_loglevel)  # set loglevel
    console_formatter = logging.Formatter(
        console_logformat
    )  # a simple console format
    console_handler.setFormatter(
        console_formatter
    )  # tell the console_handler to use this format

    # add the handlers to the root logger
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Suppress some of the overly verbose logs
    logging.getLogger("sacn").setLevel(logging.WARNING)
    logging.getLogger("aiohttp.access").setLevel(logging.WARNING)
    logging.getLogger("zeroconf").setLevel(logging.WARNING)

    global _LOGGER
    _LOGGER = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bộ điều khiển hiệu ứng đèn LED nối mạng"
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"wls {PROJECT_VERSION}",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config",
        help="Thư mục chứa các tệp cấu hình",
        default=config_helpers.get_default_config_directory(),
        type=str,
    )
    parser.add_argument(
        "--open-ui",
        dest="open_ui",
        action="store_true",
        help="Tự động mở giao diện web",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="đặt loglevel thành INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="đặt loglevel thành DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    parser.add_argument(
        "-p",
        "--port",
        dest="port",
        help="Cổng giao diện web (HTTP)",
        default=None,
        type=int,
    )
    parser.add_argument(
        "-p_s",
        "--port_secure",
        dest="port_s",
        help="Cổng giao diện web (HTTPS)",
        default=None,
        type=int,
    )
    parser.add_argument(
        "--host",
        dest="host",
        help="Địa chỉ lưu trữ giao diện web WiFi Led Studio",
        default=None,
        type=str,
    )
    parser.add_argument(
        "--tray",
        dest="tray",
        action="store_true",
        help="Ẩn bảng điều khiển WiFi Led Studio vào khay hệ thống",
    )
    parser.add_argument(
        "--performance",
        dest="performance",
        action="store_true",
        help="Hồ sơ hiệu suất của WiFi Led Studio. Nhà phát triển có thể sử dụng điều này để chẩn đoán các vấn đề về hiệu suất.",
    )
    parser.add_argument(
        "--offline",
        dest="offline_mode",
        action="store_true",
        help="Tắt cập nhật tự động và trình ghi sự cố sentry",
    )
    parser.add_argument(
        "--sentry-crash-test",
        dest="sentry_test",
        action="store_true",
        help="Điều này xảy ra sự cố. Hãy kiểm tra trình ghi sự cố sentry",
    )
    return parser.parse_args()


def main():
    """Main entry point allowing external calls"""
    args = parse_args()
    config_helpers.ensure_config_directory(args.config)
    setup_logging(args.loglevel, config_dir=args.config)
    config_helpers.load_logger()

    # Set some process priority optimisations
    p = psutil.Process(os.getpid())

    if psutil.WINDOWS:
        try:
            p.nice(psutil.HIGH_PRIORITY_CLASS)
        except psutil.Error:
            _LOGGER.info(
                "Không thể đặt mức độ ưu tiên, vui lòng chạy với tư cách Quản trị viên nếu bạn đang gặp sự cố về tốc độ khung hình"
            )
        # p.ionice(psutil.IOPRIO_HIGH)
    elif psutil.LINUX:
        try:
            p.nice(15)
            p.ionice(psutil.IOPRIO_CLASS_RT, value=7)
        except psutil.Error:
            _LOGGER.info(
                "Không thể đặt mức độ ưu tiên, vui lòng chạy dưới quyền root hoặc sudo nếu bạn đang gặp sự cố về tốc độ khung hình",
            )
    else:
        p.nice(15)

    if not currently_frozen():
        if args.offline_mode:
            _LOGGER.warning(
                "Chế độ Ngoại tuyến được Bật - Vui lòng kiểm tra các bản cập nhật thường xuyên."
            )

    if args.sentry_test:
        """This will crash Wls and submit a Sentry error if Sentry is configured"""
        _LOGGER.warning("Chỉ đạo WiFi Led Studio vào một bức tường gạch")
        div_by_zero = 1 / 0
    if args.tray or currently_frozen():
        # If pystray is imported on a device that can't display it, it explodes. Catch it
        try:
            import pystray
        except Exception as Error:
            msg = f"Lỗi: Không thể biểu tượng khay. Đang Tắt. Lỗi: {Error}"
            _LOGGER.critical(msg)
            raise Exception(msg)
            sys.exit(0)

        from PIL import Image

        if currently_frozen():
            current_directory = os.path.dirname(__file__)
            icon_location = os.path.join(current_directory, "tray.png")
        else:
            current_directory = os.path.dirname(__file__)
            icon_location = os.path.join(
                current_directory, "..", "icons/" "tray.png"
            )
        icon = pystray.Icon(
            "Wls", icon=Image.open(icon_location), title="WiFi Led Studio @ Rainbow Music Led"
        )
        icon.visible = True
    else:
        icon = None

    if icon:
        icon.run(setup=entry_point)
    else:
        entry_point()



def entry_point(icon=None):
    # have to re-parse args here :/ no way to pass them through pysicon's setup
    args = parse_args()

    exit_code = 4
    while exit_code == 4:
        _LOGGER.info("Lõi WiFi Led Studio đang khởi tạo")

        if args.performance:
            print("Thu thập dữ liệu hiệu suất...")
            yappi.start()
        wls = WlsCore(
            config_dir=args.config,
            host=args.host,
            port=args.port,
            port_s=args.port_s,
            icon=icon,
            )

        exit_code = wls.start(open_ui=args.open_ui)

        if args.performance:
            print("Đã thu thập xong dữ liệu hiệu suất")
            filename = config_helpers.get_profile_dump_location(
                config_dir=args.config
            )
            yappi.stop()
            stats = yappi.get_func_stats()
            yappi.get_thread_stats().print_all()
            stats.save(filename, type="pstat")
            print(f"Đã lưu dữ liệu hiệu suất vào thư mục cấu hình: {filename}")
            print(
                "Vui lòng gửi dữ liệu hiệu suất cho Rainbow Music Led: https://facebook.com/rainbowmusicled"
            )
    if icon:
        icon.stop()


if __name__ == "__main__":
    sys.exit(main())
