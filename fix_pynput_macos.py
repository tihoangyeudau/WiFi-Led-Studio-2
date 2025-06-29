#!/usr/bin/env python3
"""
Fix pynput installation for macOS compatibility
"""

import sys
import subprocess
import importlib
import platform

def check_pynput_installation():
    """Check current pynput installation"""
    print("🔍 Checking pynput installation...")
    
    try:
        import pynput
        version = getattr(pynput, '__version__', 'unknown')
        print(f"✅ pynput version: {version}")
        
        # Check platform-specific modules
        if platform.system() == 'Darwin':
            modules_to_check = [
                'pynput.keyboard._darwin',
                'pynput.mouse._darwin',
                'pynput._util.darwin',
                'pynput._util'
            ]
            
            available = []
            missing = []
            
            for module_name in modules_to_check:
                try:
                    importlib.import_module(module_name)
                    available.append(module_name)
                except ImportError as e:
                    missing.append((module_name, str(e)))
            
            print(f"✅ Available modules: {len(available)}")
            for mod in available:
                print(f"   - {mod}")
            
            if missing:
                print(f"❌ Missing modules: {len(missing)}")
                for mod, error in missing:
                    print(f"   - {mod}: {error}")
                return False
            
            return True
        
        return True
        
    except ImportError as e:
        print(f"❌ pynput not installed: {e}")
        return False

def install_pynput_dependencies():
    """Install pynput and its dependencies"""
    print("\n📦 Installing pynput dependencies...")
    
    commands = [
        # Uninstall existing pynput
        [sys.executable, '-m', 'pip', 'uninstall', '-y', 'pynput'],
        
        # Install system dependencies (if needed)
        # Note: On macOS, pynput should work with system Python frameworks
        
        # Install pynput with specific version
        [sys.executable, '-m', 'pip', 'install', 'pynput==1.7.6'],
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"   Step {i}: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"   ✅ Step {i} completed")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Step {i} failed: {e}")
            if i == 1:  # Uninstall might fail if not installed
                print("   (This is OK if pynput wasn't installed)")
                continue
            return False
    
    return True

def test_pynput_functionality():
    """Test pynput functionality"""
    print("\n🧪 Testing pynput functionality...")
    
    try:
        from pynput import keyboard, mouse
        
        # Test keyboard listener creation (don't start it)
        def on_press(key):
            pass
        
        def on_release(key):
            pass
        
        keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        print("✅ Keyboard listener can be created")
        
        # Test mouse listener creation (don't start it)
        def on_move(x, y):
            pass
        
        def on_click(x, y, button, pressed):
            pass
        
        mouse_listener = mouse.Listener(
            on_move=on_move,
            on_click=on_click
        )
        print("✅ Mouse listener can be created")
        
        # Test mouse controller
        mouse_controller = mouse.Controller()
        pos = mouse_controller.position
        print(f"✅ Mouse position accessible: {pos}")
        
        return True
        
    except Exception as e:
        print(f"❌ pynput functionality test failed: {e}")
        return False

def check_system_requirements():
    """Check macOS system requirements"""
    print("\n🔒 Checking macOS system requirements...")
    
    # Check if we're on macOS
    if platform.system() != 'Darwin':
        print(f"⚠️  Not on macOS (current: {platform.system()})")
        return True
    
    print(f"✅ macOS version: {platform.mac_ver()[0]}")
    
    # Check Python installation type
    python_path = sys.executable
    print(f"✅ Python path: {python_path}")
    
    if 'framework' in python_path.lower():
        print("✅ Using framework Python (recommended for pynput)")
    else:
        print("⚠️  Not using framework Python")
        print("   pynput works best with python.org installer")
        print("   Consider installing Python from https://python.org")
    
    # Check for Xcode Command Line Tools
    try:
        result = subprocess.run(['xcode-select', '--print-path'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Xcode Command Line Tools installed")
        else:
            print("⚠️  Xcode Command Line Tools not found")
            print("   Run: xcode-select --install")
    except FileNotFoundError:
        print("⚠️  xcode-select not found")
    
    return True

def suggest_alternatives():
    """Suggest alternative solutions"""
    print("\n🔧 Alternative solutions if pynput still doesn't work:")
    print()
    print("1. Use different Python installation:")
    print("   - Download from https://python.org (framework Python)")
    print("   - Avoid Homebrew Python for pynput")
    print()
    print("2. Grant accessibility permissions:")
    print("   - System Preferences > Security & Privacy > Privacy > Accessibility")
    print("   - Add Terminal.app and your built app")
    print()
    print("3. Try different pynput versions:")
    print("   pip3 install pynput==1.7.6")
    print("   pip3 install pynput==1.7.4")
    print()
    print("4. Use native macOS APIs:")
    print("   - Consider using PyObjC with Cocoa")
    print("   - Or Quartz Event Services")
    print()
    print("5. Build without hotkeys temporarily:")
    print("   - Modify hotkeys.py to disable on macOS")
    print("   - Add hotkeys back after fixing pynput")

def main():
    """Main fix function"""
    print("🍎 pynput macOS Fix Tool")
    print("=" * 30)
    
    steps = [
        ("System Requirements", check_system_requirements),
        ("Current Installation", check_pynput_installation),
        ("Install Dependencies", install_pynput_dependencies),
        ("Test Functionality", test_pynput_functionality),
        ("Final Check", check_pynput_installation),
    ]
    
    passed = 0
    total = len(steps)
    
    for step_name, step_func in steps:
        print(f"\n📍 {step_name}")
        print("-" * 20)
        
        try:
            if step_func():
                passed += 1
                print(f"✅ {step_name} passed")
            else:
                print(f"❌ {step_name} failed")
                if step_name == "Install Dependencies":
                    print("Continuing to test anyway...")
        except Exception as e:
            print(f"❌ {step_name} crashed: {e}")
    
    print("\n" + "=" * 30)
    print(f"Results: {passed}/{total} steps passed")
    
    if passed >= 3:  # At least system check + installation + one test
        print("🎉 pynput should work now!")
        print("\nTry building again:")
        print("   python3 build_minimal_macos.py")
    else:
        print("❌ pynput fix incomplete")
        suggest_alternatives()
    
    return passed >= 3

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)