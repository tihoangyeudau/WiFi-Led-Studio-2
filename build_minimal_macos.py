#!/usr/bin/env python3
"""
Minimal macOS build script - excludes problematic dependencies
"""

import os
import sys
import subprocess
import platform

def main():
    """Main build function"""
    print("🍎 WiFi Led Studio - Minimal macOS Build")
    print("=" * 40)
    
    # Check platform
    if platform.system() != 'Darwin':
        print(f"⚠️  This script is for macOS, but running on {platform.system()}")
        print("Continuing anyway...")
    
    # Step 1: Source protection
    print("\n🔐 Step 1: Source protection...")
    try:
        result = subprocess.run([sys.executable, 'simple_protect.py'], 
                              check=True, capture_output=True, text=True)
        print("✅ Source protection completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Source protection failed: {e}")
        return False
    
    # Step 2: Clean previous build
    print("\n🧹 Step 2: Cleaning previous build...")
    if os.path.exists('build_simple_protected'):
        import shutil
        shutil.rmtree('build_simple_protected')
        print("✅ Previous build cleaned")
    
    # Step 3: Minimal build
    print("\n🏗️  Step 3: Running minimal build...")
    try:
        result = subprocess.run([sys.executable, 'setup_simple_minimal.py', 'build'], 
                              check=True, text=True)
        print("✅ Minimal build completed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Minimal build failed: {e}")
        return False
    
    # Step 4: Verify
    print("\n✅ Step 4: Verifying build...")
    app_path = "build_simple_protected/WiFi Led Studio.app"
    if os.path.exists(app_path):
        print(f"✅ App bundle created: {app_path}")
        
        # Check structure
        contents_dir = os.path.join(app_path, "Contents")
        if os.path.exists(contents_dir):
            print("✅ App bundle structure OK")
            
            # List contents
            print("\n📁 App bundle contents:")
            for root, dirs, files in os.walk(app_path):
                level = root.replace(app_path, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files[:5]:  # Show first 5 files
                    print(f"{subindent}{file}")
                if len(files) > 5:
                    print(f"{subindent}... and {len(files) - 5} more files")
        
        return True
    else:
        print("❌ App bundle not found")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 Minimal build completed successfully!")
        print("\n📋 Usage:")
        print('   open "build_simple_protected/WiFi Led Studio.app"')
        print('   or double-click the app in Finder')
    else:
        print("\n❌ Build failed!")
        print("\nTry the full build script if minimal build doesn't work:")
        print("   python3 build_macos_safe.py")
    
    sys.exit(0 if success else 1)