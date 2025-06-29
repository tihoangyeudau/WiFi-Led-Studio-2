#!/usr/bin/env python3
"""
Safe macOS build script with error handling and debugging
"""

import os
import sys
import subprocess
import platform

def check_environment():
    """Check build environment"""
    print("🔍 Checking build environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print(f"❌ Python {sys.version_info.major}.{sys.version_info.minor} is too old. Need 3.8+")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Check platform
    if platform.system() != 'Darwin':
        print(f"⚠️  This script is for macOS, but running on {platform.system()}")
    
    print(f"✅ Platform: {platform.system()} {platform.machine()}")
    
    # Check required files
    required_files = [
        'wls/__main__.py',
        'setup_simple_protected.py', 
        'simple_protect.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ Required files present")
    return True

def install_dependencies():
    """Install or update dependencies"""
    print("\n📦 Checking dependencies...")
    
    dependencies = [
        ('numpy', 'numpy>=1.24.0'),
        ('cx-freeze', 'cx-freeze>=7.0.0')
    ]
    
    for module_name, pip_name in dependencies:
        try:
            module = __import__(module_name.replace('-', '_'))
            version = getattr(module, '__version__', 'unknown')
            print(f"✅ {module_name}: {version}")
        except ImportError:
            print(f"⚠️  Installing {module_name}...")
            try:
                subprocess.run([sys.executable, '-m', 'pip', 'install', pip_name], 
                             check=True, capture_output=True)
                print(f"✅ {module_name} installed")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install {module_name}: {e}")
                return False
    
    return True

def run_source_protection():
    """Run source protection step"""
    print("\n🔐 Running source protection...")
    
    try:
        result = subprocess.run([sys.executable, 'simple_protect.py'], 
                              check=True, capture_output=True, text=True)
        print("✅ Source protection completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Source protection failed:")
        print(f"   Return code: {e.returncode}")
        if e.stdout:
            print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False

def run_build():
    """Run the actual build"""
    print("\n🏗️  Running build...")
    
    # Clean previous build
    if os.path.exists('build_simple_protected'):
        import shutil
        shutil.rmtree('build_simple_protected')
        print("✅ Cleaned previous build")
    
    try:
        # Run build with verbose output
        result = subprocess.run([sys.executable, 'setup_simple_protected.py', 'build'], 
                              check=True, text=True)
        print("✅ Build completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed:")
        print(f"   Return code: {e.returncode}")
        
        # Try to provide helpful error messages
        if "No module named 'numpy.core._methods'" in str(e):
            print("\n🔧 Numpy module issue detected. Trying fixes...")
            return try_numpy_fixes()
        
        return False

def try_numpy_fixes():
    """Try various numpy-related fixes"""
    print("🔧 Attempting numpy fixes...")
    
    fixes = [
        ("Reinstall numpy", [sys.executable, '-m', 'pip', 'uninstall', '-y', 'numpy'], 
                           [sys.executable, '-m', 'pip', 'install', 'numpy']),
        ("Install specific numpy version", [sys.executable, '-m', 'pip', 'install', 'numpy==1.26.2']),
        ("Update cx-freeze", [sys.executable, '-m', 'pip', 'install', '--upgrade', 'cx-freeze'])
    ]
    
    for fix_name, *commands in fixes:
        print(f"   Trying: {fix_name}")
        try:
            for cmd in commands:
                subprocess.run(cmd, check=True, capture_output=True)
            
            # Try build again
            result = subprocess.run([sys.executable, 'setup_simple_protected.py', 'build'], 
                                  check=True, capture_output=True)
            print(f"✅ {fix_name} worked!")
            return True
            
        except subprocess.CalledProcessError:
            print(f"   {fix_name} didn't work, trying next...")
            continue
    
    print("❌ All numpy fixes failed")
    return False

def verify_build():
    """Verify the build output"""
    print("\n✅ Verifying build...")
    
    app_path = "build_simple_protected/WiFi Led Studio.app"
    exe_path = "build_simple_protected/WiFi Led Studio/WiFi Led Studio"
    
    if os.path.exists(app_path):
        print(f"✅ macOS app bundle created: {app_path}")
        
        # Check bundle structure
        contents_dir = os.path.join(app_path, "Contents")
        if os.path.exists(contents_dir):
            print("✅ App bundle structure looks good")
            
            # Check for executable
            macos_exe = os.path.join(contents_dir, "MacOS", "WiFi Led Studio")
            if os.path.exists(macos_exe):
                print("✅ Executable found in bundle")
                # Make sure it's executable
                os.chmod(macos_exe, 0o755)
            else:
                print("⚠️  Executable not found in bundle")
        
        return True
        
    elif os.path.exists(exe_path):
        print(f"✅ Executable created: {exe_path}")
        return True
    else:
        print("❌ No build output found")
        return False

def show_usage_instructions():
    """Show usage instructions"""
    print("\n📋 Usage Instructions:")
    print("=" * 40)
    
    app_path = "build_simple_protected/WiFi Led Studio.app"
    if os.path.exists(app_path):
        print(f"🍎 macOS App Bundle: {app_path}")
        print("   Double-click to run, or:")
        print(f"   open '{app_path}'")
        print()
        print("📦 Distribution:")
        print("   - Copy the .app bundle to Applications folder")
        print("   - Or create a .dmg installer")
        print("   - For distribution outside App Store, you may need code signing")
    else:
        exe_path = "build_simple_protected/WiFi Led Studio/WiFi Led Studio"
        if os.path.exists(exe_path):
            print(f"🖥️  Executable: {exe_path}")
            print("   Run with:")
            print(f"   '{exe_path}'")

def main():
    """Main build function"""
    print("🍎 WiFi Led Studio - Safe macOS Build")
    print("=" * 40)
    
    steps = [
        ("Environment Check", check_environment),
        ("Dependencies", install_dependencies),
        ("Source Protection", run_source_protection),
        ("Build", run_build),
        ("Verification", verify_build),
    ]
    
    for step_name, step_func in steps:
        print(f"\n📍 {step_name}")
        print("-" * 20)
        
        try:
            if not step_func():
                print(f"\n❌ {step_name} failed!")
                
                # Offer debug option
                response = input("Run debug script? (y/n): ").lower().strip()
                if response == 'y':
                    if os.path.exists('debug_macos_build.py'):
                        subprocess.run([sys.executable, 'debug_macos_build.py'])
                
                return False
                
        except KeyboardInterrupt:
            print(f"\n⚠️  {step_name} interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ {step_name} crashed: {e}")
            return False
    
    print("\n🎉 Build completed successfully!")
    show_usage_instructions()
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)