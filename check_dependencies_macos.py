#!/usr/bin/env python3
"""
Check all dependencies required for WiFi Led Studio on macOS
"""

import sys
import importlib
import platform

def check_dependency(name, import_name=None, required=True):
    """Check if a dependency is available"""
    if import_name is None:
        import_name = name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        status = "✅" if required else "✅"
        print(f"{status} {name}: {version}")
        return True
    except ImportError as e:
        status = "❌" if required else "⚠️ "
        print(f"{status} {name}: {e}")
        return False

def check_wls_modules():
    """Check WLS-specific modules"""
    print("\n📦 WiFi Led Studio modules:")
    print("-" * 30)
    
    # Add wls to path
    import os
    wls_path = os.path.join(os.path.dirname(__file__), 'wls')
    if wls_path not in sys.path:
        sys.path.insert(0, wls_path)
    
    wls_modules = [
        'core',
        'hotkeys', 
        'http_manager',
        'utils',
        'api',
        'api.ping'
    ]
    
    available = 0
    for module_name in wls_modules:
        try:
            importlib.import_module(module_name)
            print(f"✅ wls.{module_name}")
            available += 1
        except ImportError as e:
            print(f"❌ wls.{module_name}: {e}")
    
    return available, len(wls_modules)

def main():
    """Main check function"""
    print("🍎 WiFi Led Studio - Dependencies Check for macOS")
    print("=" * 55)
    
    print(f"🐍 Python: {sys.version}")
    print(f"🖥️  Platform: {platform.system()} {platform.release()}")
    
    # Core dependencies
    print("\n📦 Core dependencies:")
    print("-" * 20)
    
    core_deps = [
        ('aiohttp', 'aiohttp'),
        ('asyncio', 'asyncio'),
        ('requests', 'requests'),
        ('psutil', 'psutil'),
        ('serial', 'serial'),
        ('zeroconf', 'zeroconf'),
    ]
    
    core_available = 0
    for name, import_name in core_deps:
        if check_dependency(name, import_name):
            core_available += 1
    
    # Audio dependencies
    print("\n🔊 Audio dependencies:")
    print("-" * 20)
    
    audio_deps = [
        ('aubio', 'aubio'),
        ('sounddevice', 'sounddevice'),
    ]
    
    audio_available = 0
    for name, import_name in audio_deps:
        if check_dependency(name, import_name):
            audio_available += 1
    
    # Network dependencies
    print("\n🌐 Network dependencies:")
    print("-" * 20)
    
    network_deps = [
        ('icmplib', 'icmplib'),
    ]
    
    network_available = 0
    for name, import_name in network_deps:
        if check_dependency(name, import_name):
            network_available += 1
    
    # GUI dependencies
    print("\n🖼️  GUI dependencies:")
    print("-" * 20)
    
    gui_deps = [
        ('PIL/Pillow', 'PIL'),
        ('pystray', 'pystray'),
        ('pynput', 'pynput'),
    ]
    
    gui_available = 0
    for name, import_name in gui_deps:
        if check_dependency(name, import_name):
            gui_available += 1
    
    # Platform-specific modules
    print("\n🍎 macOS-specific modules:")
    print("-" * 25)
    
    macos_modules = [
        ('pynput.keyboard._darwin', 'pynput.keyboard._darwin'),
        ('pynput.mouse._darwin', 'pynput.mouse._darwin'),
        ('pystray._darwin', 'pystray._darwin'),
    ]
    
    macos_available = 0
    for name, import_name in macos_modules:
        if check_dependency(name, import_name, required=False):
            macos_available += 1
    
    # WLS modules
    wls_available, wls_total = check_wls_modules()
    
    # Summary
    print("\n" + "=" * 55)
    print("📊 Summary:")
    print(f"   Core dependencies: {core_available}/{len(core_deps)}")
    print(f"   Audio dependencies: {audio_available}/{len(audio_deps)}")
    print(f"   Network dependencies: {network_available}/{len(network_deps)}")
    print(f"   GUI dependencies: {gui_available}/{len(gui_deps)}")
    print(f"   macOS modules: {macos_available}/{len(macos_modules)}")
    print(f"   WLS modules: {wls_available}/{wls_total}")
    
    total_required = len(core_deps) + len(audio_deps) + len(network_deps) + len(gui_deps)
    total_available = core_available + audio_available + network_available + gui_available
    
    print(f"\n🎯 Overall: {total_available}/{total_required} required dependencies")
    
    if total_available == total_required and wls_available == wls_total:
        print("🎉 All dependencies are available! Build should work.")
        return True
    elif total_available >= total_required - 1:
        print("⚠️  Most dependencies available. Build might work.")
        return True
    else:
        print("❌ Missing critical dependencies. Build will likely fail.")
        
        # Suggest fixes
        print("\n🔧 Suggested fixes:")
        if network_available == 0:
            print("   pip3 install icmplib")
        if gui_available < len(gui_deps):
            print("   pip3 install pillow pystray pynput")
        if audio_available < len(audio_deps):
            print("   pip3 install aubio sounddevice")
        if macos_available == 0:
            print("   Run: python3 fix_pynput_macos.py")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)