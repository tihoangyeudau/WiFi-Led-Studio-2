#!/usr/bin/env python3
"""
cx_Freeze setup with simple source protection (bytecode only)
Cross-platform support: Windows, macOS, Linux
"""

import os
import sys
import platform
from cx_Freeze import setup, Executable

# Base directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Check if we have protected source
protected_dir = os.path.join(base_dir, "protected_source")
if not os.path.exists(protected_dir):
    print("❌ Protected source not found!")
    print("Please run: python simple_protect.py first")
    sys.exit(1)

try:
    print("🔐 Building with bytecode-protected source...")
except UnicodeEncodeError:
    print("Building with bytecode-protected source...")

# Detect platform
current_platform = platform.system().lower()
is_windows = current_platform == 'windows'
is_macos = current_platform == 'darwin'
is_linux = current_platform == 'linux'

def get_numpy_includes():
    """Get numpy includes that work across different numpy versions"""
    numpy_includes = []
    
    try:
        import numpy
        numpy_version = numpy.__version__
        
        # Basic numpy modules that should always work
        basic_includes = [
            'numpy.core', 'numpy.lib', 'numpy.random',
            'numpy.fft', 'numpy.linalg', 'numpy.ma'
        ]
        
        # Version-specific modules to try
        optional_includes = [
            'numpy.core._methods',
            'numpy._distributor_init',
            'numpy.core._multiarray_umath',
            'numpy.core.multiarray',
            'numpy.core.umath'
        ]
        
        # Add basic includes
        numpy_includes.extend(basic_includes)
        
        # Try to include optional modules safely
        for module_name in optional_includes:
            try:
                __import__(module_name)
                numpy_includes.append(module_name)
            except ImportError:
                # Skip modules that don't exist in this numpy version
                pass
        
        print(f"   Numpy version: {numpy_version}")
        print(f"   Numpy includes: {len(numpy_includes)} modules")
        
        # Special handling for macOS numpy issues
        if is_macos:
            # Remove problematic modules on macOS
            problematic_modules = ['numpy.core._methods']
            numpy_includes = [mod for mod in numpy_includes if mod not in problematic_modules]
            print(f"   macOS: Filtered to {len(numpy_includes)} safe modules")
        
    except ImportError:
        print("   Warning: numpy not found, skipping numpy-specific includes")
    
    return numpy_includes

def get_pystray_includes():
    """Get pystray includes that work on current platform"""
    pystray_includes = ['pystray', 'pystray._base']
    
    try:
        import pystray
        
        # Try platform-specific modules
        if is_windows:
            try:
                import pystray._win32
                pystray_includes.extend(['pystray._win32', 'pystray._util.win32'])
            except ImportError:
                pass
        elif is_macos:
            try:
                import pystray._darwin
                pystray_includes.append('pystray._darwin')
            except ImportError:
                pass
            # Don't include pystray._util.darwin as it may not exist
        elif is_linux:
            try:
                import pystray._xorg
                pystray_includes.append('pystray._xorg')
            except ImportError:
                pass
        
        print(f"   Pystray includes: {len(pystray_includes)} modules")
        
    except ImportError:
        print("   Warning: pystray not found")
    
    return pystray_includes

try:
    print(f"🖥️  Platform detected: {platform.system()} ({platform.machine()})")
except UnicodeEncodeError:
    print(f"Platform detected: {platform.system()} ({platform.machine()})")

# Platform-specific packages
platform_packages = []
platform_includes = []

if is_windows:
    platform_packages.extend([
        'win32api', 'win32gui', 'win32process', 'win32ui', 'win32com',
        'pythoncom', 'pywintypes', 'comtypes', 'pycaw'
    ])
    platform_includes.extend([
        'win32api', 'win32gui', 'win32con', 'win32clipboard',
        'pythoncom', 'pywintypes'
    ])
elif is_macos:
    platform_packages.extend([
        'AppKit', 'Foundation', 'Cocoa', 'objc'
    ])
    platform_includes.extend([
        # macOS-specific numpy fixes
        'numpy._distributor_init',
    ])
elif is_linux:
    platform_packages.extend([
        'gi', 'gi.repository'
    ])
    platform_includes.extend([
        'pystray._xorg', 'pystray._util.xorg'
    ])

# Build options
build_options = {
    'packages': [
        # Core Python packages
        'asyncio', 'aiohttp', 'aiohttp_cors', 'json', 'logging',
        'multiprocessing', 'threading', 'time', 'os', 'sys', 'pathlib',
        'urllib', 'socket', 'ssl', 'hashlib', 'base64', 'zlib', 'pickle',
        'sqlite3', 'uuid', 'datetime', 'collections', 'itertools',
        'functools', 'operator', 'math', 'random', 'struct', 'binascii',
        'hmac', 'secrets', 'tempfile', 'shutil', 'glob', 'fnmatch',
        'subprocess', 'signal', 'atexit', 'weakref', 'gc', 'ctypes',
        'platform', 'traceback', 'warnings', 'copy', 're', 'string',
        'textwrap', 'io', 'contextlib', 'types', 'inspect', 'importlib',
        'pkgutil', 'email', 'html', 'http', 'urllib.parse', 'urllib.request',
        'urllib.error',
        
        # Third-party packages
        'certifi', 'charset_normalizer', 'idna', 'requests', 'numpy', 'PIL',
        'pystray', 'pynput', 'psutil', 'serial', 'zeroconf', 'ifaddr',
        'paho.mqtt', 'voluptuous', 'yaml', 'aubio', 'sounddevice',
        'samplerate', 'sentry_sdk', 'icmplib', 'bokeh', 'tornado',
        'jinja2', 'markupsafe', 'packaging', 'contourpy', 'xyzservices',
        'cairocffi', 'cairosvg', 'cffi', 'pycparser', 'cssselect2',
        'defusedxml', 'tinycss2', 'webencodings',
    ] + platform_packages,
    'includes': [
        # Common includes
        'PIL', 'PIL.Image', 'PIL.ImageDraw',
        'aubio', 'sounddevice',
        'sentry_sdk.integrations.logging', 'icmplib.sockets',
        'bokeh.io', 'tornado.web', 'jinja2.ext',
    ] + platform_includes + get_numpy_includes() + get_pystray_includes(),
    'excludes': [
        # GUI frameworks we don't use
        'tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'wx',
        
        # Development and testing
        'unittest', 'test', 'pytest', 'nose', 'coverage',
        'distutils', 'setuptools', 'pip', 'wheel',
        'cx_Freeze', 'pyinstaller',
        
        # Documentation
        'sphinx', 'docutils', 'pydoc',
        
        # Interactive environments
        'IPython', 'jupyter', 'notebook', 'qtconsole',
        
        # Test modules
        'matplotlib.tests', 'numpy.tests', 'scipy.tests',
        'pandas.tests', 'PIL.tests', 'tornado.test',
        'aiohttp.test_utils', 'bokeh.tests', 'gevent.tests',
        'psutil.tests', 'win32com.test', 'comtypes.test',
        
        # Numpy modules that might cause issues
        'numpy.core._methods', 'numpy.core._multiarray_tests',
        'numpy.core._operand_flag_tests', 'numpy.core._rational_tests',
        'numpy.core._struct_ufunc_tests', 'numpy.core._umath_tests',
        'numpy.distutils', 'numpy.f2py', 'numpy.testing',
        
        # Other potentially problematic modules
        'curses', 'readline', 'rlcompleter',
        'pdb', 'bdb', 'cmd', 'code',
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
    'build_exe': f'build_simple_protected/WiFi Led Studio',
    'silent': True,
}

# Platform-specific executable configuration
def get_executable_config():
    """Get platform-specific executable configuration"""
    config = {
        'script': 'wls/__main__.py',
        'copyright': '© 2024 WiFi Led Studio',
        'shortcut_name': 'WiFi Led Studio',
    }
    
    if is_windows:
        config.update({
            'base': 'Win32GUI',
            'target_name': 'WiFi Led Studio.exe',
            'icon': os.path.join(base_dir, 'icons', 'wifiledstudio.ico'),
            'shortcut_dir': 'DesktopFolder',
        })
    elif is_macos:
        config.update({
            'base': None,
            'target_name': 'WiFi Led Studio',
            'icon': os.path.join(base_dir, 'icons', 'WiFi Led Studio.icns'),
        })
    else:  # Linux
        config.update({
            'base': None,
            'target_name': 'WiFi Led Studio',
            'icon': os.path.join(base_dir, 'icons', 'wifiledstudio.png'),
        })
    
    return config

# Executable configuration
executable_config = get_executable_config()
executables = [Executable(**executable_config)]

def create_macos_app_bundle():
    """Create macOS .app bundle after cx-freeze build"""
    if not is_macos:
        return
    
    import shutil
    import plistlib
    
    build_dir = build_options['build_exe']
    app_name = 'WiFi Led Studio.app'
    app_path = os.path.join(os.path.dirname(build_dir), app_name)
    
    try:
        print(f"🍎 Creating macOS .app bundle: {app_path}")
    except UnicodeEncodeError:
        print(f"Creating macOS .app bundle: {app_path}")
    
    # Create .app structure
    contents_dir = os.path.join(app_path, 'Contents')
    macos_dir = os.path.join(contents_dir, 'MacOS')
    resources_dir = os.path.join(contents_dir, 'Resources')
    
    os.makedirs(macos_dir, exist_ok=True)
    os.makedirs(resources_dir, exist_ok=True)
    
    # Move cx-freeze build to MacOS directory
    if os.path.exists(build_dir):
        # Copy all files from build directory to MacOS
        for item in os.listdir(build_dir):
            src = os.path.join(build_dir, item)
            dst = os.path.join(macos_dir, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
    
    # Create Info.plist
    info_plist = {
        'CFBundleName': 'WiFi Led Studio',
        'CFBundleDisplayName': 'WiFi Led Studio',
        'CFBundleIdentifier': 'com.wifiledstudio.app',
        'CFBundleVersion': '2.0.0',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleExecutable': 'WiFi Led Studio',
        'CFBundleIconFile': 'WiFi Led Studio.icns',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'WLST',
        'LSMinimumSystemVersion': '10.15.0',
        'LSUIElement': True,  # Hide from dock
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'NSMicrophoneUsageDescription': 'WiFi Led Studio needs microphone access to capture audio for light effects and visualizations',
        'NSAppleEventsUsageDescription': 'WiFi Led Studio needs to control other applications to synchronize light effects with media playback',
        'NSLocalNetworkUsageDescription': 'WiFi Led Studio needs to discover and control WiFi lighting devices on your local network',
        'NSCameraUsageDescription': 'WiFi Led Studio does not use the camera, but the audio framework may require this permission',
        'NSBonjourServices': [
            '_http._tcp',
            '_tcp',
            '_udp',
            '_rml._tcp',
            '_services._dns-sd._udp'
        ]
    }
    
    plist_path = os.path.join(contents_dir, 'Info.plist')
    with open(plist_path, 'wb') as f:
        plistlib.dump(info_plist, f)
    
    # Copy icon if exists
    icon_src = os.path.join(base_dir, 'icons', 'WiFi Led Studio.icns')
    if os.path.exists(icon_src):
        shutil.copy2(icon_src, os.path.join(resources_dir, 'WiFi Led Studio.icns'))
    
    # Make executable
    executable_path = os.path.join(macos_dir, 'WiFi Led Studio')
    if os.path.exists(executable_path):
        os.chmod(executable_path, 0o755)
    
    try:
        print(f"✅ macOS .app bundle created successfully!")
        print(f"📦 Location: {app_path}")
    except UnicodeEncodeError:
        print(f"macOS .app bundle created successfully!")
        print(f"Location: {app_path}")
    
    # Clean up original build directory
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

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
        f'Operating System :: {platform.system()}',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.12',
        'Topic :: System :: Hardware',
        'Topic :: Multimedia :: Graphics',
    ],
    options={'build_exe': build_options},
    executables=executables,
)

# Post-build: Create macOS .app bundle
if is_macos and 'build' in sys.argv:
    create_macos_app_bundle()