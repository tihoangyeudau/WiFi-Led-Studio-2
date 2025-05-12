# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import copy_metadata

spec_root = os.path.abspath(SPECPATH)
datas = [
         (f'C:/Users/tuant/AppData/Local/Programs/Python/Python312/Scripts/build/exe.win-amd64-3.12/lib/wls','wls/'),
         (f'C:/Users/tuant/AppData/Local/Programs/Python/Python312/Scripts/build/exe.win-amd64-3.12/lib/wls_frontend','wls_frontend/'),
         (f'C:/Users/tuant/AppData/Local/Programs/Python/Python312/Scripts/build/exe.win-amd64-3.12/lib/xyzservices','xyzservices/'),
         (f'{spec_root}/icons','icons/'),
         (f'{spec_root}/icons/tray.png','.')
      ]
datas += copy_metadata('bokeh')

venv_root = os.path.abspath(os.path.join(SPECPATH, '..'))
block_cipher = None
print(venv_root)

a = Analysis([f'{spec_root}\\wls\\__main__.py'],
             pathex=[f'{spec_root}', f'{spec_root}\\wls'],
             binaries=[],
             datas=datas,
             hiddenimports=[
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
                           "pycaw",
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
                           "pystray._win32",
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
          name='WiFi Led Studio',
          debug=False,
          bootloader_ignore_signals=True,
          strip=False,
          upx=False,   # Disable UPX compression which can trigger AV
          console=False,
          windowed=True,
          icon=(f'{spec_root}\\icons\\wifiledstudio.ico'),
          version=f'{spec_root}\\version_file.txt' if os.path.exists(f'{spec_root}\\version_file.txt') else None,
          uac_admin=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,  # Disable UPX compression
               upx_exclude=[],
               name='WiFi Led Studio')