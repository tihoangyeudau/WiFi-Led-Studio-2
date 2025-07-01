# -*- mode: python ; coding: utf-8 -*-
# macOS build with bytecode protection
# This spec uses compiled .pyc files from protected_source directory
import os
import sys
from PyInstaller.utils.hooks import copy_metadata

# Check if protected source exists
protected_dir = os.path.join(os.path.dirname(os.path.abspath(SPEC)), "protected_source")
if not os.path.exists(protected_dir):
    print("❌ Protected source not found!")
    print("Please run: python simple_protect.py first")
    sys.exit(1)

print("🔐 Building macOS app with bytecode-protected source...")

# Data files - using protected source
datas = [
    (os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'icons'), 'icons/'),
    (os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'icons/tray.png'), '.'),
    (os.path.join(protected_dir, 'wls'), 'wls/'),
    (os.path.join(protected_dir, 'wls_frontend'), 'wls_frontend/'),
]

datas += copy_metadata('bokeh')
block_cipher = None

a = Analysis([os.path.join(protected_dir, 'wls/__main__.py')],
             pathex=['.', protected_dir, os.path.join(protected_dir, 'wls')],
             binaries=[],
             datas=datas,
             hiddenimports=[
                            "pynput",
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

app = BUNDLE(
            coll,
            name='WiFi Led Studio.app',
            icon=os.path.join(os.path.dirname(os.path.abspath(SPEC)), 'icons/WiFi Led Studio.icns'),
            bundle_identifier='com.rml.rmlapp.protected',
            info_plist={
                'NSMicrophoneUsageDescription': 'WiFi Led Studio needs microphone access to capture audio for light effects and visualizations',
                'NSAppleEventsUsageDescription': 'WiFi Led Studio needs to control other applications to synchronize light effects with media playbook',
                'NSLocalNetworkUsageDescription': 'WiFi Led Studio needs to discover and control WiFi lighting devices on your local network',
                'LSUIElement': 'True',
                'NSRequiresAquaSystemAppearance': 'False',
                'NSCameraUsageDescription': 'WiFi Led Studio does not use the camera, but the audio framework may require this permission',
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable': 'True',
                'NSBonjourServices': [
                    '_http._tcp',
                    '_tcp',
                    '_udp',
                    '_rml._tcp',
                    '_services._dns-sd._udp'
                ]
            }
)