#!/usr/bin/env python3
"""
cx_Freeze setup with simple source protection (bytecode only)
"""

import os
import sys
from cx_Freeze import setup, Executable

# Base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Check if we have protected source
protected_dir = os.path.join(base_dir, "protected_source")
if not os.path.exists(protected_dir):
    print("❌ Protected source not found!")
    print("Please run: python simple_protect.py first")
    sys.exit(1)

print("🔐 Building with bytecode-protected source...")

# Build options
build_options = {
    'packages': [
        'asyncio',
        'aiohttp',
        'aiohttp_cors',
        'json',
        'logging',
        'multiprocessing',
        'threading',
        'time',
        'os',
        'sys',
        'pathlib',
        'urllib',
        'socket',
        'ssl',
        'hashlib',
        'base64',
        'zlib',
        'pickle',
        'sqlite3',
        'uuid',
        'datetime',
        'collections',
        'itertools',
        'functools',
        'operator',
        'math',
        'random',
        'struct',
        'binascii',
        'hmac',
        'secrets',
        'tempfile',
        'shutil',
        'glob',
        'fnmatch',
        'subprocess',
        'signal',
        'atexit',
        'weakref',
        'gc',
        'ctypes',
        'platform',
        'traceback',
        'warnings',
        'copy',
        're',
        'string',
        'textwrap',
        'io',
        'contextlib',
        'types',
        'inspect',
        'importlib',
        'pkgutil',
        'email',
        'html',
        'http',
        'urllib.parse',
        'urllib.request',
        'urllib.error',
        'certifi',
        'charset_normalizer',
        'idna',
        'requests',
        'numpy',
        'PIL',
        'pystray',
        'pynput',
        'psutil',
        'serial',
        'zeroconf',
        'ifaddr',
        'paho.mqtt',
        'voluptuous',
        'yaml',
        'aubio',
        'sounddevice',
        'samplerate',
        'pycaw',
        'comtypes',
        'win32api',
        'win32gui',
        'win32process',
        'win32ui',
        'win32com',
        'pythoncom',
        'pywintypes',
        'sentry_sdk',
        'icmplib',
        'bokeh',
        'tornado',
        'jinja2',
        'markupsafe',
        'packaging',
        'contourpy',
        'xyzservices',
        'cairocffi',
        'cairosvg',
        'cffi',
        'pycparser',
        'cssselect2',
        'defusedxml',
        'tinycss2',
        'webencodings',
    ],
    'includes': [
        'pystray',
        'pystray._win32',
        'pystray._util',
        'pystray._util.win32',
        'pystray._base',
        'win32api',
        'win32gui',
        'win32con',
        'win32clipboard',
        'pythoncom',
        'pywintypes',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'numpy.core._methods',
        'aubio',
        'sounddevice',
        'sentry_sdk.integrations.logging',
        'icmplib.sockets',
        'bokeh.io',
        'tornado.web',
        'jinja2.ext',
    ],
    'excludes': [
        'tkinter',
        'unittest',
        'test',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
    ],
    'include_files': [
        # Use protected source (bytecode)
        (os.path.join(protected_dir, 'wls'), 'lib/wls'),
        (os.path.join(protected_dir, 'wls_frontend'), 'lib/wls_frontend'),
        (os.path.join(base_dir, 'icons'), 'icons'),
        # Copy tray.png to multiple locations
        (os.path.join(base_dir, 'icons', 'tray.png'), 'tray.png'),
        (os.path.join(base_dir, 'icons', 'tray.png'), 'lib/tray.png'),
        (os.path.join(base_dir, 'icons', 'tray.png'), 'lib/wls/tray.png'),
    ],
    'optimize': 2,  # Maximum optimization
    'build_exe': 'build_simple_protected/WiFi Led Studio',
    'silent': True,
}

# Executable configuration
executables = [
    Executable(
        script='wls/__main__.py',
        base='Win32GUI' if sys.platform == 'win32' else None,
        target_name='WiFi Led Studio.exe' if sys.platform == 'win32' else 'WiFi Led Studio',
        icon=os.path.join(base_dir, 'icons', 'wifiledstudio.ico') if sys.platform == 'win32' else None,
        copyright='© 2024 WiFi Led Studio',
        shortcut_name='WiFi Led Studio',
        shortcut_dir='DesktopFolder',
    )
]

# Setup
setup(
    name='WiFi Led Studio',
    version='2.0.0',
    description='WiFi Led Studio - Bytecode Protected',
    long_description='WiFi Led Studio with source code compiled to bytecode for protection.',
    author='WiFi Led Studio Team',
    author_email='support@wifiledstudio.com',
    url='https://wifiledstudio.com',
    license='Proprietary',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'License :: Other/Proprietary License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Hardware',
        'Topic :: Multimedia :: Graphics',
    ],
    options={'build_exe': build_options},
    executables=executables,
)