# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import copy_metadata
datas = [   ('/Users/rainbowmusicled/Documents/GitHub/WiFi-Led-Studio-2/icons', 'icons/'),
            ('/Users/rainbowmusicled/Documents/GitHub/WiFi-Led-Studio-2/icons/tray.png', '.'),
            ('/usr/local/bin/build/WiFi Led Studio-3.3.7.app/Contents/MacOS/lib/wls', 'wls/'),
            ('/usr/local/bin/build/WiFi Led Studio-3.3.7.app/Contents/MacOS/lib/wls_frontend', 'wls_frontend/'),
            ('/usr/local/bin/build/WiFi Led Studio-3.3.7.app/Contents/MacOS/lib/xyzservices', 'xyzservices/'),
            ('/usr/local/bin/build/WiFi Led Studio-3.3.7.app/Contents/MacOS/lib/stupidArtnet', 'stupidArtnet/'),]
datas += copy_metadata('bokeh')


block_cipher = None

a = Analysis(['./wls/__main__.py'],
             pathex=['.', './wls'],
             binaries=[],
             datas=datas,
             hiddenimports=[
                            "sacn",
                            "stupidArtnet",
                            "aubio",
                            "numpy",
                            "math",
                            "voluptuous",
                            "numpy",
                            "numpy.core",
                            "numpy.core.multiarray",
                            "aiohttp",
                            "cchardet",
                            "paho",
                            "paho.mqtt",
                            "paho.mqtt.client",
                            "samplerate",
                            "sounddevice",
                            "_sounddevice_data",
                            "sentry_sdk",
                            "sentry_sdk.integrations.django",
                            "sentry_sdk.integrations.flask",
                            "sentry_sdk.integrations.bottle",
                            "sentry_sdk.integrations.falcon",
                            "sentry_sdk.integrations.sanic",
                            "sentry_sdk.integrations.celery",
                            "sentry_sdk.integrations.aiohttp",
                            "sentry_sdk.integrations.rq",
                            "sentry_sdk.integrations.tornado",
                            "sentry_sdk.integrations.sqlalchemy",
                            "sentry_sdk.integrations.boto3",
                            "_cffi_backend",
                            "serial",
                            "pystray",
                            "pystray._darwin",
                            "serial.tools.list_ports",
                            "icmplib",
                            "aiohttp_cors",
                            "psutil",
                            ],
             runtime_hooks=[],
             excludes=[
                      "PyQt5", "PyQt6", "PySide2", "PySide6",
                      "IPython", "pytest", "sphinx",
                      "pyi_rth", "pyimod", "pyi-windows-manifest-filename",
                      "pyiboot", "pyinstaller"
                      ],
             cipher=block_cipher,
             noarchive=False)

# Remove PyInstaller specific resource files that trigger detections
for i in range(len(a.binaries)):
      if "pyi-" in a.binaries[i][0] or "_pyi_" in a.binaries[i][0]:
          a.binaries[i] = (a.binaries[i][0].replace("pyi-", "py-"), a.binaries[i][1], a.binaries[i][2])

# Clean pyinstaller metadata from the binary
for i in range(len(a.datas)):
      if "pyi-" in a.datas[i][0]:
          a.datas[i] = (a.datas[i][0].replace("pyi-", "py-"), a.datas[i][1], a.datas[i][2])

pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name = 'WiFi Led Studio',
          debug=False,
          bootloader_ignore_signals=True,
          strip=False,
          upx=False,
          console=False,
          windowed=True)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               upx_exclude=[],
               name='WiFi Led Studio',)
app = BUNDLE(coll,
            name = 'WiFi Led Studio.app',
            icon = '/Users/rainbowmusicled/Documents/GitHub/WiFi-Led-Studio-2/icons/WiFi Led Studio.icns',
            bundle_identifier = 'com.rml.wls',
            info_plist = {
                'NSHighResolutionCapable': 'True',
                'NSMicrophoneUsageDescription': 'WiFi Led Studio needs microphone access to capture audio for light effects and visualizations',
                'LSUIElement': 'True',
                'UIApplicationExitsOnSuspend': 'True',
                'NSRequiresAquaSystemAppearance': 'False',
                'NSAppleEventsUsageDescription': 'WiFi Led Studio needs to control system audio settings',
                'NSCameraUsageDescription': 'WiFi Led Studio does not use the camera',
                'NSBluetoothAlwaysUsageDescription': 'WiFi Led Studio uses Bluetooth to connect to some LED controllers',
            }
)

