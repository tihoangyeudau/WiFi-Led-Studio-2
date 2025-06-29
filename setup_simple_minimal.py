#!/usr/bin/env python3
"""
Minimal setup script for macOS with fewer dependencies
"""

import os
import sys
import platform
from cx_Freeze import setup, Executable

# Check for protected source
protected_dir = 'protected_source'
if not os.path.exists(protected_dir):
    print("❌ Protected source not found!")
    print("Please run: python simple_protect.py first")
    sys.exit(1)

print("🔐 Building with minimal dependencies...")

# Detect platform
current_platform = platform.system().lower()
is_macos = current_platform == 'darwin'

print(f"🖥️  Platform: {platform.system()} ({platform.machine()})")

def get_pynput_includes():
    """Get pynput includes for current platform"""
    pynput_includes = []

    try:
        import pynput

        if is_macos:
            # Try to import macOS-specific modules
            macos_modules = [
                'pynput.keyboard._darwin',
                'pynput.mouse._darwin',
                'pynput._util.darwin',
                'pynput._util'
            ]

            for module_name in macos_modules:
                try:
                    __import__(module_name)
                    pynput_includes.append(module_name)
                    print(f"   ✅ Found: {module_name}")
                except ImportError:
                    print(f"   ⚠️  Missing: {module_name}")

        print(f"   Pynput includes: {len(pynput_includes)} modules")

    except ImportError:
        print("   Warning: pynput not found")

    return pynput_includes

# Base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Minimal build options
build_options = {
    'packages': [
        # Core packages only
        'aiohttp', 'aiohttp_cors', 'asyncio',
        'json', 'logging', 'os', 'sys', 'platform',
        'threading', 'time', 'datetime',
        'urllib', 'http', 'socket',
        'serial', 'zeroconf',
        # Audio (essential)
        'aubio', 'sounddevice',
        # System monitoring
        'psutil',
        # HTTP requests
        'requests',
        # Network utilities
        'icmplib',
        # MQTT
        'paho.mqtt',
        # Input handling
        'pynput',
        # System tray
        'pystray',
        # Image processing
        'PIL',
    ],
    'includes': [
        # Minimal includes
        'aubio', 'sounddevice',
        'serial', 'zeroconf',
        'psutil',
        'requests',
        # Network utilities
        'icmplib', 'icmplib.sockets',
        # MQTT
        'paho.mqtt', 'paho.mqtt.client',
        # Image processing
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        # System tray
        'pystray', 'pystray._base',
    ] + get_pynput_includes(),
    'excludes': [
        # Exclude problematic modules
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'matplotlib', 'scipy', 'pandas',
        'numpy.core._methods', 'numpy.testing',
        'pystray._util.darwin', 'pystray._util.win32',
        'unittest', 'test', 'pytest',
        'sphinx', 'docutils',
        'IPython', 'jupyter',
        'distutils', 'setuptools', 'pip',
    ],
    'include_files': [
        # Use protected source (bytecode)
        (os.path.join(protected_dir, 'wls'), 'lib/wls'),
        (os.path.join(protected_dir, 'wls_frontend'), 'lib/wls_frontend'),
        (os.path.join(base_dir, 'icons'), 'icons'),
    ],
    'optimize': 2,
    'build_exe': f'build_simple_protected/WiFi Led Studio',
    'silent': True,
}

# Executable configuration
executable_config = {
    'script': 'wls/__main__.py',
    'copyright': '© 2024 WiFi Led Studio',
}

if is_macos:
    executable_config.update({
        'base': None,  # Console app for macOS
        'target_name': 'WiFi Led Studio',
        'icon': os.path.join(base_dir, 'icons', 'WiFi Led Studio.icns') if os.path.exists(os.path.join(base_dir, 'icons', 'WiFi Led Studio.icns')) else None,
    })
else:
    executable_config.update({
        'base': 'Win32GUI' if platform.system() == 'Windows' else None,
        'target_name': 'WiFi Led Studio.exe' if platform.system() == 'Windows' else 'WiFi Led Studio',
        'icon': os.path.join(base_dir, 'icons', 'wifiledstudio.ico') if os.path.exists(os.path.join(base_dir, 'icons', 'wifiledstudio.ico')) else None,
    })

# Create executable
executable = Executable(**executable_config)

# Run setup
setup(
    name='WiFi Led Studio',
    version='2.0.0',
    description='WiFi Led Studio - Minimal Build',
    author='WiFi Led Studio Team',
    options={'build_exe': build_options},
    executables=[executable]
)

# Post-build processing for macOS
if is_macos and os.path.exists(build_options['build_exe']):
    print("🍎 Creating minimal macOS .app bundle...")

    import shutil
    import plistlib

    build_dir = build_options['build_exe']
    app_name = 'WiFi Led Studio.app'
    app_path = os.path.join(os.path.dirname(build_dir), app_name)

    # Remove existing app bundle
    if os.path.exists(app_path):
        shutil.rmtree(app_path)

    # Create app bundle structure
    contents_dir = os.path.join(app_path, 'Contents')
    macos_dir = os.path.join(contents_dir, 'MacOS')
    resources_dir = os.path.join(contents_dir, 'Resources')

    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)

    # Move build contents to appropriate directories
    for item in os.listdir(build_dir):
        src = os.path.join(build_dir, item)

        # Resources go to Resources directory
        if item == 'icons':
            # Only copy tray.png and other needed icons, not the app icon
            dst_icons_dir = os.path.join(resources_dir, 'icons')
            os.makedirs(dst_icons_dir, exist_ok=True)

            # Copy specific files from icons directory
            for icon_file in os.listdir(src):
                if icon_file != 'WiFi Led Studio.icns':  # Skip app icon, will be copied separately
                    icon_src = os.path.join(src, icon_file)
                    icon_dst = os.path.join(dst_icons_dir, icon_file)
                    if os.path.isfile(icon_src):
                        shutil.copy2(icon_src, icon_dst)
        # Everything else goes to MacOS directory
        else:
            dst = os.path.join(macos_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

    # Create minimal Info.plist
    info_plist = {
        'CFBundleName': 'WiFi Led Studio',
        'CFBundleDisplayName': 'WiFi Led Studio',
        'CFBundleIdentifier': 'com.wifiledstudio.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleExecutable': 'WiFi Led Studio',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'WLST',
        'LSMinimumSystemVersion': '10.15',
        'LSUIElement': True,  # Run in background
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
    }

    # Write Info.plist
    plist_path = os.path.join(contents_dir, 'Info.plist')
    with open(plist_path, 'wb') as f:
        plistlib.dump(info_plist, f)

    # Copy app icon to Resources directory (required for macOS app bundle)
    icon_src = os.path.join(base_dir, 'icons', 'WiFi Led Studio.icns')
    if os.path.exists(icon_src):
        icon_dst = os.path.join(resources_dir, 'WiFi Led Studio.icns')
        shutil.copy2(icon_src, icon_dst)
        info_plist['CFBundleIconFile'] = 'WiFi Led Studio.icns'
        # Update plist with icon
        with open(plist_path, 'wb') as f:
            plistlib.dump(info_plist, f)

    # Make executable
    executable_path = os.path.join(macos_dir, 'WiFi Led Studio')
    if os.path.exists(executable_path):
        os.chmod(executable_path, 0o755)

    # Remove original build directory
    shutil.rmtree(build_dir)

    print(f"✅ Minimal macOS .app bundle created: {app_path}")

print("✅ Minimal build completed!")