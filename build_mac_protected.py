#!/usr/bin/env python3
"""
Build script for macOS with bytecode protection
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def check_macos():
    """Check if running on macOS"""
    if sys.platform != 'darwin':
        print("❌ This script is for macOS only!")
        print(f"Current platform: {sys.platform}")
        return False
    return True

def check_dependencies():
    """Check if required tools are available"""
    print("🔍 Checking dependencies...")

    # Check Python
    try:
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False

    # Check PyInstaller
    try:
        result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ PyInstaller {result.stdout.strip()}")
        else:
            print("❌ PyInstaller not found!")
            print("Install with: pip install pyinstaller")
            return False
    except FileNotFoundError:
        print("❌ PyInstaller not found!")
        print("Install with: pip install pyinstaller")
        return False

    return True

def build_protected():
    """Main build function"""
    print("🔐 WiFi Led Studio - macOS Protected Build")
    print("==========================================")
    print()

    # Check platform
    if not check_macos():
        return False

    # Check dependencies
    if not check_dependencies():
        return False

    # Get base directory
    base_dir = Path(__file__).parent.absolute()
    os.chdir(base_dir)

    # Step 1: Create protected source
    print("🔒 Step 1: Creating bytecode-protected source...")
    if not run_command("python3 simple_protect.py", "Source protection"):
        return False

    # Verify protected source exists
    protected_dir = base_dir / "protected_source"
    if not protected_dir.exists():
        print("❌ Protected source directory not created!")
        return False

    # Step 2: Clean previous builds
    print("🧹 Step 2: Cleaning previous builds...")
    dist_dir = base_dir / "dist"
    build_dir = base_dir / "build"

    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("  ✓ Removed dist directory")

    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("  ✓ Removed build directory")

    # Step 3: Build with PyInstaller
    print("📦 Step 3: Building macOS app with PyInstaller...")
    if not run_command("pyinstaller mac_protected.spec --clean --noconfirm", "PyInstaller build"):
        return False

    # Step 4: Verify the build
    print("🔍 Step 4: Verifying build...")
    app_path = dist_dir / "WiFi Led Studio.app"

    if app_path.exists():
        print("✅ Build successful!")
        print(f"📂 Output: {app_path}")

        # Show app info
        print()
        print("📋 App Information:")
        print("   Name: WiFi Led Studio")
        print("   Bundle ID: com.rml.rmlapp.protected")
        print(f"   Location: {app_path}")

        # Check app size
        try:
            result = subprocess.run(['du', '-sh', str(app_path)], capture_output=True, text=True)
            if result.returncode == 0:
                app_size = result.stdout.split()[0]
                print(f"   Size: {app_size}")
        except:
            pass

        print()
        print("🚀 To run the app:")
        print(f"   open '{app_path}'")

        # Make the build script executable
        build_script = base_dir / "build_mac_protected.sh"
        if build_script.exists():
            os.chmod(build_script, 0o755)

        return True
    else:
        print("❌ Build failed - app not found!")
        return False

def main():
    """Main entry point"""
    success = build_protected()

    if success:
        print()
        print("🎉 macOS Protected Build Complete!")
        sys.exit(0)
    else:
        print()
        print("💥 Build Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()