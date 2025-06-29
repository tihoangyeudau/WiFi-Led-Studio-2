#!/usr/bin/env python3
"""
Fix accessibility permissions for pynput on macOS
"""

import sys
import subprocess
import os

def check_accessibility_permissions():
    """Check if accessibility permissions are granted"""
    print("🔒 Checking accessibility permissions...")
    
    try:
        from pynput import mouse
        
        # Try to get mouse position
        controller = mouse.Controller()
        pos = controller.position
        print(f"✅ Mouse position accessible: {pos}")
        print("✅ Accessibility permissions appear to be granted")
        return True
        
    except Exception as e:
        print(f"❌ Accessibility test failed: {e}")
        return False

def show_permission_instructions():
    """Show detailed instructions for granting permissions"""
    print("\n🔧 How to Grant Accessibility Permissions:")
    print("=" * 50)
    print()
    print("1. 🍎 Open System Preferences")
    print("   - Click Apple menu > System Preferences")
    print("   - Or press Cmd+Space, type 'System Preferences'")
    print()
    print("2. 🔒 Go to Security & Privacy")
    print("   - Click on 'Security & Privacy' icon")
    print()
    print("3. 🔐 Navigate to Privacy tab")
    print("   - Click on 'Privacy' tab at the top")
    print()
    print("4. ♿ Select Accessibility")
    print("   - In the left sidebar, click 'Accessibility'")
    print()
    print("5. 🔓 Unlock to make changes")
    print("   - Click the lock icon in bottom-left")
    print("   - Enter your admin password")
    print()
    print("6. ➕ Add applications")
    print("   - Click the '+' button")
    print("   - Navigate to and add these apps:")
    print("     • Terminal.app (for testing)")
    print("     • WiFi Led Studio.app (your built app)")
    print()
    print("7. ✅ Enable the apps")
    print("   - Make sure both apps are checked")
    print("   - Lock the preferences again")
    print()
    print("8. 🔄 Restart the applications")
    print("   - Quit and restart Terminal")
    print("   - Quit and restart WiFi Led Studio")

def test_with_permissions():
    """Test pynput functionality with permissions"""
    print("\n🧪 Testing pynput with permissions...")
    
    try:
        from pynput import keyboard, mouse
        
        # Test mouse controller
        mouse_controller = mouse.Controller()
        pos = mouse_controller.position
        print(f"✅ Mouse position: {pos}")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ pynput test failed: {e}")
        return False

def check_app_permissions(app_path):
    """Check if the built app has permissions"""
    if not os.path.exists(app_path):
        print(f"⚠️  App not found: {app_path}")
        return False
    
    print(f"\n📱 Checking app permissions: {app_path}")
    
    # Try to run the app briefly to test permissions
    executable_path = os.path.join(app_path, "Contents", "MacOS", "WiFi Led Studio")
    
    if not os.path.exists(executable_path):
        print(f"❌ Executable not found: {executable_path}")
        return False
    
    print("ℹ️  To test app permissions:")
    print(f"   1. Add '{app_path}' to Accessibility")
    print("   2. Run the app")
    print("   3. Check for pynput warnings in console")
    
    return True

def open_system_preferences():
    """Open System Preferences to Security & Privacy"""
    print("\n🚀 Opening System Preferences...")
    
    try:
        # Try to open directly to Security & Privacy
        subprocess.run([
            'open', 
            'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
        ], check=True)
        print("✅ System Preferences opened to Accessibility")
        return True
    except subprocess.CalledProcessError:
        try:
            # Fallback: open System Preferences normally
            subprocess.run(['open', '/System/Applications/System Preferences.app'], check=True)
            print("✅ System Preferences opened")
            print("   Navigate to: Security & Privacy > Privacy > Accessibility")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to open System Preferences: {e}")
            return False

def main():
    """Main function"""
    print("🍎 WiFi Led Studio - Accessibility Permissions Fix")
    print("=" * 55)
    
    # Check current permissions
    if check_accessibility_permissions():
        print("\n🎉 Accessibility permissions are already working!")
        
        # Test pynput functionality
        if test_with_permissions():
            print("✅ pynput should work correctly")
            
            # Check built app if it exists
            app_path = "build_simple_protected/WiFi Led Studio.app"
            check_app_permissions(app_path)
            
            return True
        else:
            print("⚠️  pynput tests failed despite permissions")
    
    else:
        print("\n❌ Accessibility permissions needed")
        
        # Show instructions
        show_permission_instructions()
        
        # Offer to open System Preferences
        print("\n" + "=" * 55)
        response = input("🤔 Open System Preferences now? (y/n): ").lower().strip()
        
        if response in ['y', 'yes']:
            if open_system_preferences():
                print("\n✅ System Preferences opened")
                print("Follow the instructions above to grant permissions")
                print("Then run this script again to test")
            else:
                print("❌ Failed to open System Preferences")
                print("Please open it manually and follow the instructions")
        else:
            print("ℹ️  Please grant permissions manually when ready")
    
    return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n📋 Summary:")
        print("1. Grant accessibility permissions as shown above")
        print("2. Run this script again to test: python3 fix_accessibility_macos.py")
        print("3. Rebuild if needed: python3 build_macos_with_hotkeys.py")
    
    sys.exit(0 if success else 1)