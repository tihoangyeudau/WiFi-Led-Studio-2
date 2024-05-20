# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import copy_metadata
datas = [('/Users/phamtuantrung/Documents/GitHub/WiFi-Led-Studio-2/icons', 'icons/'), ('/Users/phamtuantrung/Documents/GitHub/WiFi-Led-Studio-2/icons/tray.png', '.'),
             ('/usr/local/bin/build/WiFi Led Studio-3.2.4.app/Contents/MacOS/lib/wls', 'wls/'),
             ('/usr/local/bin/build/WiFi Led Studio-3.2.4.app/Contents/MacOS/lib/wls_frontend', 'wls_frontend/'),
             ('/usr/local/bin/build/WiFi Led Studio-3.2.4.app/Contents/MacOS/lib/xyzservices', 'xyzservices/'),
             ('/usr/local/bin/build/WiFi Led Studio-3.2.4.app/Contents/MacOS/lib/stupidArtnet', 'stupidArtnet/')]
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
                            "aiohttp",
                            "cchardet",
                            "paho",
                            "paho.mqtt",
                            "openrgb-python",
                            "openrgb",
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
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name = 'WiFi Led Studio',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          windowed=True,)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='WiFi Led Studio',)
app = BUNDLE(coll,
            name = 'WiFi Led Studio.app',
            icon = '/Users/phamtuantrung/Documents/GitHub/WiFi-Led-Studio-2/icons/WiFi Led Studio.icns',
            bundle_identifier = 'com.rml.wls',
            info_plist = {
                'NSHighResolutionCapable': 'True',
                'NSMicrophoneUsageDescription': 'Access Microphone',
                'LSUIElement': 'True',
                'UIApplicationExitsOnSuspend': 'True',
            }
)

