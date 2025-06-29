#!/usr/bin/env python3
"""
Install missing dependencies for WiFi Led Studio on macOS
"""

import sys
import subprocess
import importlib

def check_dependency(import_name):
    """Check if a dependency is available"""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False

def install_package(package_name, import_name=None):
    """Install a package using pip"""
    if import_name is None:
        import_name = package_name

    if check_dependency(import_name):
        print(f"✅ {package_name} already installed")
        return True

    print(f"📦 Installing {package_name}...")
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', package_name
        ], check=True, capture_output=True, text=True)

        # Verify installation
        if check_dependency(import_name):
            print(f"✅ {package_name} installed successfully")
            return True
        else:
            print(f"⚠️  {package_name} installed but import failed")
            return False

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def main():
    """Main installation function"""
    print("🍎 WiFi Led Studio - Dependencies Installer for macOS")
    print("=" * 55)

    # List of required packages
    packages = [
        # Core packages
        ('aiohttp', 'aiohttp'),
        ('requests', 'requests'),
        ('psutil', 'psutil'),
        ('pyserial', 'serial'),
        ('zeroconf', 'zeroconf'),

        # Audio packages
        ('aubio', 'aubio'),
        ('sounddevice', 'sounddevice'),

        # Network packages
        ('icmplib', 'icmplib'),
        ('paho-mqtt', 'paho.mqtt'),

        # GUI packages
        ('pillow', 'PIL'),
        ('pystray', 'pystray'),
        ('pynput', 'pynput'),

        # Build tools
        ('cx-freeze', 'cx_Freeze'),
    ]

    print("🔍 Checking and installing dependencies...")
    print("-" * 40)

    installed = 0
    failed = 0

    for package_name, import_name in packages:
        if install_package(package_name, import_name):
            installed += 1
        else:
            failed += 1

    print("\n" + "=" * 55)
    print(f"📊 Installation Summary:")
    print(f"   ✅ Successful: {installed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📦 Total: {len(packages)}")

    if failed == 0:
        print("\n🎉 All dependencies installed successfully!")
        print("\nNext steps:")
        print("1. Run dependency check: python3 check_dependencies_macos.py")
        print("2. Build the app: python3 build_macos_with_hotkeys.py")
        return True
    else:
        print(f"\n⚠️  {failed} packages failed to install")
        print("\nTroubleshooting:")
        print("1. Check Python installation")
        print("2. Install Xcode Command Line Tools: xcode-select --install")
        print("3. Try installing failed packages manually")
        print("4. Consider using conda instead of pip")
        return False

def install_system_dependencies():
    """Install system-level dependencies"""
    print("\n🔧 System Dependencies:")
    print("-" * 25)

    # Check for Xcode Command Line Tools
    try:
        result = subprocess.run(['xcode-select', '--print-path'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Xcode Command Line Tools already installed")
        else:
            print("⚠️  Installing Xcode Command Line Tools...")
            subprocess.run(['xcode-select', '--install'])
    except FileNotFoundError:
        print("❌ xcode-select not found")

    # Check for Homebrew (optional)
    try:
        result = subprocess.run(['brew', '--version'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Homebrew available")

            # Suggest some useful packages
            print("💡 Optional: Install audio libraries via Homebrew:")
            print("   brew install portaudio")
            print("   brew install aubio")
        else:
            print("ℹ️  Homebrew not installed (optional)")
    except FileNotFoundError:
        print("ℹ️  Homebrew not installed (optional)")

if __name__ == "__main__":
    install_system_dependencies()
    success = main()
    sys.exit(0 if success else 1)