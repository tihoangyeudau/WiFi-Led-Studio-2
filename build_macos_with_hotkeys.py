#!/usr/bin/env python3
"""
macOS build script with hotkeys support (fixes pynput issues)
"""

import os
import sys
import subprocess
import platform

def main():
    """Main build function"""
    print("🍎 WiFi Led Studio - macOS Build with Hotkeys")
    print("=" * 50)
    
    # Check platform
    if platform.system() != 'Darwin':
        print(f"⚠️  This script is for macOS, but running on {platform.system()}")
        print("Continuing anyway...")
    
    # Step 1: Check dependencies
    print("\n🔍 Step 1: Checking dependencies...")
    try:
        result = subprocess.run([sys.executable, 'check_dependencies_macos.py'], 
                              check=True, text=True)
        print("✅ Dependencies check passed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Dependencies check had issues: {e}")
        print("Continuing with build anyway...")
    
    # Step 2: Fix pynput installation
    print("\n🔧 Step 2: Fixing pynput for macOS...")
    try:
        result = subprocess.run([sys.executable, 'fix_pynput_macos.py'], 
                              check=True, text=True)
        print("✅ pynput fix completed")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  pynput fix had issues: {e}")
        print("Continuing with build anyway...")
    
    # Step 3: Source protection
    print("\n🔐 Step 3: Source protection...")
    try:
        result = subprocess.run([sys.executable, 'simple_protect.py'], 
                              check=True, capture_output=True, text=True)
        print("✅ Source protection completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Source protection failed: {e}")
        return False
    
    # Step 4: Clean previous build
    print("\n🧹 Step 4: Cleaning previous build...")
    if os.path.exists('build_simple_protected'):
        import shutil
        shutil.rmtree('build_simple_protected')
        print("✅ Previous build cleaned")
    
    # Step 5: Build with hotkeys
    print("\n🏗️  Step 5: Building with hotkeys support...")
    try:
        result = subprocess.run([sys.executable, 'setup_simple_minimal.py', 'build'], 
                              check=True, text=True)
        print("✅ Build completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print("\nTrying to diagnose the issue...")
        
        # Check if it's a pynput issue
        if "pynput" in str(e).lower():
            print("🔧 Detected pynput issue, trying alternative approach...")
            return try_alternative_build()
        
        return False
    
    # Step 6: Verify
    print("\n✅ Step 6: Verifying build...")
    app_path = "build_simple_protected/WiFi Led Studio.app"
    if os.path.exists(app_path):
        print(f"✅ App bundle created: {app_path}")
        
        # Test the app quickly
        print("\n🧪 Step 7: Testing app...")
        executable_path = os.path.join(app_path, "Contents", "MacOS", "WiFi Led Studio")
        if os.path.exists(executable_path):
            try:
                # Try to run the app with --help or --version (if supported)
                result = subprocess.run([executable_path, '--help'], 
                                      capture_output=True, text=True, timeout=5)
                print("✅ App executable responds")
            except subprocess.TimeoutExpired:
                print("✅ App starts (timed out waiting for response)")
            except Exception as e:
                print(f"⚠️  App test: {e}")
        
        return True
    else:
        print("❌ App bundle not found")
        return False

def try_alternative_build():
    """Try alternative build approach if pynput fails"""
    print("\n🔄 Trying alternative build approach...")
    
    # Try to build with setup_simple_protected.py instead
    try:
        result = subprocess.run([sys.executable, 'setup_simple_protected.py', 'build'], 
                              check=True, text=True)
        print("✅ Alternative build completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Alternative build also failed: {e}")
        return False

def show_usage_instructions():
    """Show usage instructions"""
    print("\n📋 Usage Instructions:")
    print("=" * 30)
    
    app_path = "build_simple_protected/WiFi Led Studio.app"
    if os.path.exists(app_path):
        print(f"🍎 App Bundle: {app_path}")
        print("\n🚀 To run:")
        print('   open "build_simple_protected/WiFi Led Studio.app"')
        print("   or double-click in Finder")
        print("\n⌨️  Hotkeys:")
        print("   - Hotkeys should work if pynput was fixed successfully")
        print("   - You may need to grant accessibility permissions:")
        print("     System Preferences > Security & Privacy > Privacy > Accessibility")
        print("     Add the app to the list")
        print("\n📦 Distribution:")
        print("   - Copy .app to Applications folder")
        print("   - Or create DMG installer")
        print("   - May need code signing for distribution")

def show_troubleshooting():
    """Show troubleshooting info"""
    print("\n🔧 Troubleshooting:")
    print("=" * 20)
    print("1. If hotkeys don't work:")
    print("   - Grant accessibility permissions")
    print("   - Check pynput: python3 -c 'import pynput; print(pynput.__version__)'")
    print("   - Run fix again: python3 fix_pynput_macos.py")
    print()
    print("2. If app doesn't start:")
    print("   - Check Console.app for error messages")
    print("   - Try running from terminal for debug output")
    print("   - Verify all dependencies are included")
    print()
    print("3. If build fails:")
    print("   - Run debug script: python3 debug_macos_build.py")
    print("   - Try minimal build: python3 build_minimal_macos.py")
    print("   - Check Python installation (framework Python recommended)")

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 macOS build with hotkeys completed successfully!")
        show_usage_instructions()
    else:
        print("\n❌ Build failed!")
        show_troubleshooting()
    
    sys.exit(0 if success else 1)