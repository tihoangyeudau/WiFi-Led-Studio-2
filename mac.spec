# -*- mode: python ; coding: utf-8 -*-
import os
import sys

spec_root = os.path.join(os.path.dirname(sys.argv[0]), "file")
block_cipher = None
print(spec_root)

a = Analysis(['/Users/macos/Documents/GitHub/WiFi-Led-Studio-2/wls/__main__.py'],
             pathex=[spec_root, 'spec_root/wls'],
             binaries=[],
             datas=[('/Users/macos/Documents/GitHub/WiFi-Led-Studio-2/icons', 'icons/'), ('/Users/macos/Documents/GitHub/WiFi-Led-Studio-2/icons/tray.png', '.'),
             ('/Users/macos/Documents/GitHub/WiFi-Led-Studio-2/wls', 'wls/'),
             ('/Users/macos/Documents/GitHub/WiFi-Led-Studio-2/wls_frontend', 'wls_frontend/')],
             hiddenimports=['cffi', 'pycparser',  'sacn', 'aubio', 'numpy', 'math', 'voluptuous', 'numpy', 'aiohttp', 'mido','mido.frozen', 'paho', 'paho.mqtt', 'python-rtmidi','rtmidi', 'mido.backends.rtmidi', 'paho.mqtt.client','sounddevice',
             'sentry_sdk', 'sentry_sdk.integrations.django','sentry_sdk.integrations.flask','sentry_sdk.integrations.bottle','sentry_sdk.integrations.falcon','sentry_sdk.integrations.sanic',
             'sentry_sdk.integrations.celery','sentry_sdk.integrations.aiohttp','sentry_sdk.integrations.rq','sentry_sdk.integrations.tornado','sentry_sdk.integrations.sqlalchemy',
             'sentry_sdk.integrations.boto3','_cffi_backend','serial','serial.tools.list_ports','tcp_latency','aiohttp_cors','psutil','yappi'],
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
          name = 'WiFiLedStudio',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True,
          windowed=True,)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='WiFiLedStudio',)
app = BUNDLE(coll,
            name = 'WiFiLedStudio.app',
            icon = '/Users/macos/make setup/WiFi Led Studio.icns',
            bundle_identifier = 'com.rml.wls',
            info_plist = {
                'NSHighResolutionCapable': 'True'
            }
)

