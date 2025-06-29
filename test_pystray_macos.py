#!/usr/bin/env python3
"""
Test pystray modules on macOS
"""

import sys
import importlib

def test_pystray_imports():
    """Test various pystray import combinations"""
    print("🖼️  Testing pystray imports on macOS...")
    
    # Test basic import
    try:
        import pystray
        print("✅ pystray base import: OK")
    except ImportError as e:
        print(f"❌ pystray base import failed: {e}")
        return False
    
    # Test modules that should exist
    required_modules = [
        'pystray._base',
    ]
    
    # Test platform-specific modules
    macos_modules = [
        'pystray._darwin',
        'pystray._util',
    ]
    
    # Test optional modules
    optional_modules = [
        'pystray._util.darwin',
        'pystray._util.cocoa',
    ]
    
    print("\n📋 Required modules:")
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
            return False
    
    print("\n📋 macOS-specific modules:")
    macos_available = 0
    for module_name in macos_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
            macos_available += 1
        except ImportError as e:
            print(f"❌ {module_name}: {e}")
    
    print("\n📋 Optional modules:")
    for module_name in optional_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ {module_name}")
        except ImportError as e:
            print(f"⚠️  {module_name}: {e}")
    
    # We need at least one macOS-specific module
    if macos_available == 0:
        print("\n❌ No macOS-specific pystray modules found!")
        return False
    
    return True

def test_pystray_functionality():
    """Test basic pystray functionality"""
    print("\n🧪 Testing pystray functionality...")
    
    try:
        import pystray
        from PIL import Image
        
        # Create a simple test icon
        image = Image.new('RGB', (64, 64), color='red')
        
        # Try to create a menu (don't show it)
        menu = pystray.Menu(
            pystray.MenuItem("Test", lambda: None)
        )
        
        # Try to create an icon object (don't run it)
        icon = pystray.Icon("test", image, menu=menu)
        
        print("✅ pystray objects can be created")
        return True
        
    except Exception as e:
        print(f"❌ pystray functionality test failed: {e}")
        return False

def suggest_pystray_fixes():
    """Suggest fixes for pystray issues"""
    print("\n🔧 Suggested pystray fixes:")
    print()
    print("1. Reinstall pystray:")
    print("   pip3 uninstall pystray")
    print("   pip3 install pystray")
    print()
    print("2. Install with specific version:")
    print("   pip3 install pystray==0.19.4")
    print()
    print("3. Install from source:")
    print("   pip3 install git+https://github.com/moses-palmer/pystray.git")
    print()
    print("4. Check system dependencies:")
    print("   - Ensure Xcode Command Line Tools are installed")
    print("   - xcode-select --install")
    print()
    print("5. Alternative: Use different system tray library")
    print("   - Consider rumps for macOS-specific apps")
    print("   - pip3 install rumps")

def main():
    """Main test function"""
    print("🍎 pystray macOS Compatibility Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_pystray_imports),
        ("Functionality Test", test_pystray_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed < total:
        suggest_pystray_fixes()
    else:
        print("🎉 pystray should work with cx-freeze!")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)