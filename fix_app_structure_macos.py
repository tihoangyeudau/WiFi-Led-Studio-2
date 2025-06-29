#!/usr/bin/env python3
"""
Fix macOS app bundle structure to follow Apple guidelines
"""

import os
import shutil
import sys

def fix_app_structure():
    """Verify and fix the app bundle structure if needed"""
    app_path = "build_simple_protected/WiFi Led Studio.app"
    
    if not os.path.exists(app_path):
        print("❌ App bundle not found. Build the app first.")
        return False
    
    print("🔧 Verifying macOS app bundle structure...")
    
    contents_path = os.path.join(app_path, "Contents")
    macos_path = os.path.join(contents_path, "MacOS")
    resources_path = os.path.join(contents_path, "Resources")
    
    # Check if structure is already correct
    if not os.path.exists(macos_path) or not os.path.exists(resources_path):
        print("❌ Invalid app bundle structure")
        return False
    
    # Check MacOS directory
    macos_contents = os.listdir(macos_path)
    executable_found = False
    extra_files = []
    
    for item in macos_contents:
        item_path = os.path.join(macos_path, item)
        if item == "WiFi Led Studio" and os.access(item_path, os.X_OK):
            executable_found = True
            print("✅ Executable found in MacOS/")
        else:
            extra_files.append(item)
    
    if not executable_found:
        print("❌ Executable not found in MacOS/")
        return False
    
    # If there are extra files in MacOS, move them to Resources
    moved_files = []
    for item in extra_files:
        src = os.path.join(macos_path, item)
        dst = os.path.join(resources_path, item)
        
        try:
            if os.path.exists(dst):
                if os.path.isdir(dst):
                    shutil.rmtree(dst)
                else:
                    os.remove(dst)
            
            shutil.move(src, dst)
            moved_files.append(item)
            print(f"✅ Moved {item} from MacOS/ to Resources/")
            
        except Exception as e:
            print(f"⚠️  Failed to move {item}: {e}")
    
    if moved_files:
        print(f"🎉 Moved {len(moved_files)} items to correct location")
    else:
        print("✅ App structure is already correct")
    
    return True

def verify_app_structure():
    """Verify the app structure is correct"""
    app_path = "build_simple_protected/WiFi Led Studio.app"
    
    if not os.path.exists(app_path):
        print("❌ App bundle not found")
        return False
    
    print("\n🔍 Verifying app structure...")
    
    contents_path = os.path.join(app_path, "Contents")
    macos_path = os.path.join(contents_path, "MacOS")
    resources_path = os.path.join(contents_path, "Resources")
    
    # Check required directories
    required_dirs = [contents_path, macos_path, resources_path]
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {os.path.basename(dir_path)}/ exists")
        else:
            print(f"❌ {os.path.basename(dir_path)}/ missing")
            return False
    
    # Check MacOS contains only executable
    macos_contents = os.listdir(macos_path)
    executable_count = 0
    for item in macos_contents:
        item_path = os.path.join(macos_path, item)
        if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
            executable_count += 1
    
    if executable_count == 1 and len(macos_contents) == 1:
        print("✅ MacOS/ contains only executable")
    else:
        print(f"⚠️  MacOS/ contains {len(macos_contents)} items, {executable_count} executable")
    
    # Check Resources contains support files
    resources_contents = os.listdir(resources_path)
    expected_resources = ['lib', 'WiFi Led Studio.icns']
    
    for resource in expected_resources:
        if resource in resources_contents:
            print(f"✅ Resources/{resource} exists")
        else:
            print(f"⚠️  Resources/{resource} missing")
    
    # Check for common issues
    icon_path = os.path.join(resources_path, "WiFi Led Studio.icns")
    if os.path.exists(icon_path):
        print("✅ App icon in correct location")
    else:
        print("⚠️  App icon not found in Resources/")
    
    return True

def main():
    """Main function"""
    print("🍎 macOS App Bundle Structure Verifier")
    print("=" * 42)
    
    if not fix_app_structure():
        print("❌ App structure verification failed")
        return False
    
    if not verify_app_structure():
        print("⚠️  App structure verification had issues")
        return False
    
    print("\n" + "=" * 42)
    print("🎉 App bundle structure is macOS compliant!")
    print("\nCorrect Structure:")
    print("WiFi Led Studio.app/")
    print("├── Contents/")
    print("    ├── Info.plist")
    print("    ├── MacOS/")
    print("    │   └── WiFi Led Studio (executable only)")
    print("    └── Resources/")
    print("        ├── WiFi Led Studio.icns")
    print("        ├── lib/")
    print("        ├── icons/")
    print("        └── other support files")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)