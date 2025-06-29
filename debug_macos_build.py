#!/usr/bin/env python3
"""
Debug script for macOS build issues
"""

import sys
import platform
import importlib

def check_python_version():
    """Check Python version"""
    print(f"🐍 Python version: {sys.version}")
    print(f"🖥️  Platform: {platform.platform()}")
    print(f"📍 Python executable: {sys.executable}")
    
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print("✅ Python version OK")
        return True

def check_numpy():
    """Check numpy installation and modules"""
    print("\n📊 Checking numpy...")
    
    try:
        import numpy
        print(f"✅ Numpy version: {numpy.__version__}")
        print(f"📍 Numpy location: {numpy.__file__}")
        
        # Check problematic modules
        problematic_modules = [
            'numpy.core._methods',
            'numpy.core._multiarray_tests',
            'numpy._distributor_init',
            'numpy.core',
            'numpy.lib',
            'numpy.random'
        ]
        
        available = []
        missing = []
        
        for module in problematic_modules:
            try:
                importlib.import_module(module)
                available.append(module)
            except ImportError as e:
                missing.append((module, str(e)))
        
        print(f"✅ Available numpy modules: {len(available)}")
        for mod in available:
            print(f"   - {mod}")
        
        if missing:
            print(f"⚠️  Missing numpy modules: {len(missing)}")
            for mod, error in missing:
                print(f"   - {mod}: {error}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Numpy not found: {e}")
        return False

def check_cx_freeze():
    """Check cx-freeze installation"""
    print("\n🧊 Checking cx-freeze...")
    
    try:
        import cx_Freeze
        print(f"✅ cx-Freeze version: {cx_Freeze.__version__}")
        print(f"📍 cx-Freeze location: {cx_Freeze.__file__}")
        
        # Check if we can import the freezer
        try:
            from cx_Freeze.freezer import Freezer
            print("✅ Freezer class available")
        except ImportError as e:
            print(f"❌ Freezer import failed: {e}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ cx-Freeze not found: {e}")
        return False

def check_other_dependencies():
    """Check other important dependencies"""
    print("\n📦 Checking other dependencies...")
    
    dependencies = [
        'aiohttp',
        'aubio', 
        'PIL',
        'pystray',
        'sounddevice',
        'psutil',
        'requests',
        'serial',
        'zeroconf'
    ]
    
    available = []
    missing = []
    
    for dep in dependencies:
        try:
            module = importlib.import_module(dep)
            version = getattr(module, '__version__', 'unknown')
            available.append((dep, version))
        except ImportError:
            missing.append(dep)
    
    print(f"✅ Available dependencies: {len(available)}")
    for dep, version in available:
        print(f"   - {dep}: {version}")
    
    if missing:
        print(f"⚠️  Missing dependencies: {len(missing)}")
        for dep in missing:
            print(f"   - {dep}")
    
    return len(missing) == 0

def check_build_files():
    """Check if required build files exist"""
    print("\n📁 Checking build files...")
    
    import os
    
    required_files = [
        'wls/__main__.py',
        'setup_simple_protected.py',
        'simple_protect.py',
        'icons/WiFi Led Studio.icns',
        'entitlements.xml'
    ]
    
    existing = []
    missing = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            existing.append(file_path)
        else:
            missing.append(file_path)
    
    print(f"✅ Existing files: {len(existing)}")
    for file_path in existing:
        print(f"   - {file_path}")
    
    if missing:
        print(f"❌ Missing files: {len(missing)}")
        for file_path in missing:
            print(f"   - {file_path}")
    
    return len(missing) == 0

def test_numpy_import():
    """Test specific numpy imports that cause issues"""
    print("\n🧪 Testing problematic numpy imports...")
    
    test_imports = [
        "import numpy",
        "import numpy.core",
        "import numpy.lib", 
        "import numpy.random",
        "from numpy.core import _methods",
        "import numpy._distributor_init"
    ]
    
    for test_import in test_imports:
        try:
            exec(test_import)
            print(f"✅ {test_import}")
        except ImportError as e:
            print(f"❌ {test_import}: {e}")
        except Exception as e:
            print(f"⚠️  {test_import}: {e}")

def suggest_fixes():
    """Suggest potential fixes"""
    print("\n🔧 Suggested fixes for macOS build issues:")
    print()
    print("1. Update dependencies:")
    print("   pip3 install --upgrade numpy cx-freeze")
    print()
    print("2. Install with specific versions:")
    print("   pip3 install numpy==1.26.2 cx-freeze==7.2.2")
    print()
    print("3. Use conda instead of pip:")
    print("   conda install numpy cx-freeze")
    print()
    print("4. Try alternative build method:")
    print("   pyinstaller mac.spec")
    print()
    print("5. Clean install:")
    print("   pip3 uninstall numpy cx-freeze")
    print("   pip3 install numpy cx-freeze")
    print()
    print("6. Check for conflicting installations:")
    print("   which python3")
    print("   python3 -m pip list | grep numpy")

def main():
    """Main debug function"""
    print("🔍 macOS Build Debug Tool")
    print("=" * 40)
    
    checks = [
        ("Python Version", check_python_version),
        ("Numpy", check_numpy),
        ("cx-Freeze", check_cx_freeze),
        ("Other Dependencies", check_other_dependencies),
        ("Build Files", check_build_files),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        print("-" * 20)
        try:
            if check_func():
                passed += 1
        except Exception as e:
            print(f"❌ {check_name} check failed: {e}")
    
    # Always run numpy import test
    test_numpy_import()
    
    print("\n" + "=" * 40)
    print(f"Debug Results: {passed}/{total} checks passed")
    
    if passed < total:
        suggest_fixes()
    else:
        print("🎉 All checks passed! Build should work.")
        print("If build still fails, try running with verbose output:")
        print("python3 setup_simple_protected.py build --verbose")

if __name__ == "__main__":
    main()