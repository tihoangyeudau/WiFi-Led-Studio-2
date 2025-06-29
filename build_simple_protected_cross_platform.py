#!/usr/bin/env python3
"""
Cross-platform build script for WiFi Led Studio
Automatically detects platform and runs appropriate build script
"""

import os
import sys
import platform
import subprocess

def get_platform_info():
    """Get platform information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    return {
        'system': system,
        'machine': machine,
        'is_windows': system == 'windows',
        'is_macos': system == 'darwin',
        'is_linux': system == 'linux',
        'is_64bit': machine in ['x86_64', 'amd64', 'arm64', 'aarch64']
    }

def run_windows_build():
    """Run Windows PowerShell build script"""
    print("🪟 Running Windows build script...")
    try:
        result = subprocess.run([
            'powershell.exe', 
            '-ExecutionPolicy', 'Bypass',
            '-File', 'build_simple_protected.ps1'
        ], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Windows build failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ PowerShell not found. Please install PowerShell or run build_simple_protected.ps1 manually.")
        return False

def run_macos_build():
    """Run macOS bash build script"""
    print("🍎 Running macOS build script...")
    
    # Make script executable
    script_path = 'build_simple_protected.sh'
    try:
        os.chmod(script_path, 0o755)
    except OSError:
        pass
    
    try:
        result = subprocess.run(['bash', script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ macOS build failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Bash not found. Please run build_simple_protected.sh manually.")
        return False

def run_linux_build():
    """Run Linux build (similar to macOS)"""
    print("🐧 Running Linux build script...")
    
    # Make script executable
    script_path = 'build_simple_protected.sh'
    try:
        os.chmod(script_path, 0o755)
    except OSError:
        pass
    
    try:
        result = subprocess.run(['bash', script_path], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Linux build failed: {e}")
        return False
    except FileNotFoundError:
        print("❌ Bash not found. Please run build_simple_protected.sh manually.")
        return False

def main():
    """Main build function"""
    print("🚀 WiFi Led Studio - Cross-Platform Protected Build")
    print("=" * 55)
    
    # Get platform info
    platform_info = get_platform_info()
    
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    print(f"🏗️  Architecture: {platform.machine()}")
    print(f"🐍 Python: {platform.python_version()}")
    print("")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required!")
        sys.exit(1)
    
    # Check if we're in the right directory
    if not os.path.exists('wls') or not os.path.exists('setup_simple_protected.py'):
        print("❌ Please run this script from the WiFi Led Studio root directory!")
        sys.exit(1)
    
    # Run platform-specific build
    success = False
    
    if platform_info['is_windows']:
        success = run_windows_build()
    elif platform_info['is_macos']:
        success = run_macos_build()
    elif platform_info['is_linux']:
        success = run_linux_build()
    else:
        print(f"❌ Unsupported platform: {platform.system()}")
        print("Supported platforms: Windows, macOS, Linux")
        sys.exit(1)
    
    if success:
        print("")
        print("🎉 Cross-platform build completed successfully!")
        
        # Show build output location
        if platform_info['is_windows']:
            print("📦 Build location: build_simple_protected\\WiFi Led Studio\\")
        elif platform_info['is_macos']:
            print("📦 Build location: build_simple_protected/WiFi Led Studio.app")
        else:  # Linux
            print("📦 Build location: build_simple_protected/WiFi Led Studio/")
    else:
        print("")
        print("❌ Build failed! Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()