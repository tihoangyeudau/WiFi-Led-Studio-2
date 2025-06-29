#!/usr/bin/env python3
"""
Fix encoding issues for WiFi Led Studio on macOS
"""

import os
import sys
import locale

def check_system_encoding():
    """Check system encoding settings"""
    print("🔤 System Encoding Check:")
    print("-" * 25)
    
    # Check Python encoding
    print(f"Python default encoding: {sys.getdefaultencoding()}")
    print(f"Python filesystem encoding: {sys.getfilesystemencoding()}")
    
    # Check locale
    try:
        current_locale = locale.getlocale()
        print(f"Current locale: {current_locale}")
        
        preferred_encoding = locale.getpreferredencoding()
        print(f"Preferred encoding: {preferred_encoding}")
    except Exception as e:
        print(f"Locale check failed: {e}")
    
    # Check environment variables
    env_vars = ['LANG', 'LC_ALL', 'LC_CTYPE', 'PYTHONIOENCODING']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")

def test_unicode_output():
    """Test Unicode output"""
    print("\n🌐 Unicode Output Test:")
    print("-" * 22)
    
    test_strings = [
        "ASCII text",
        "Tiếng Việt: àáạảãâầấậẩẫăằắặẳẵ",
        "More Vietnamese: èéẹẻẽêềếệểễìíịỉĩ",
        "Even more: òóọỏõôồốộổỗơờớợởỡ",
        "Final: ùúụủũưừứựửữỳýỵỷỹđ"
    ]
    
    for i, text in enumerate(test_strings, 1):
        try:
            print(f"Test {i}: {text}")
        except UnicodeEncodeError as e:
            print(f"Test {i}: FAILED - {e}")
        except Exception as e:
            print(f"Test {i}: ERROR - {e}")

def create_encoding_wrapper():
    """Create a wrapper script that sets proper encoding"""
    wrapper_content = '''#!/bin/bash
# WiFi Led Studio Encoding Wrapper for macOS

# Set UTF-8 encoding
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LC_CTYPE=en_US.UTF-8
export PYTHONIOENCODING=utf-8

# Get the directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Run the actual app
exec "$DIR/WiFi Led Studio" "$@"
'''
    
    app_path = "build_simple_protected/WiFi Led Studio.app"
    if os.path.exists(app_path):
        wrapper_path = os.path.join(app_path, "Contents", "MacOS", "WiFi Led Studio Wrapper")
        
        try:
            with open(wrapper_path, 'w', encoding='utf-8') as f:
                f.write(wrapper_content)
            
            # Make executable
            os.chmod(wrapper_path, 0o755)
            
            print(f"✅ Created encoding wrapper: {wrapper_path}")
            print("   You can run this instead of the main executable")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create wrapper: {e}")
            return False
    else:
        print(f"⚠️  App not found: {app_path}")
        return False

def fix_info_plist():
    """Fix Info.plist to include UTF-8 support"""
    app_path = "build_simple_protected/WiFi Led Studio.app"
    plist_path = os.path.join(app_path, "Contents", "Info.plist")
    
    if not os.path.exists(plist_path):
        print(f"⚠️  Info.plist not found: {plist_path}")
        return False
    
    try:
        # Read current plist
        with open(plist_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if LSEnvironment already exists
        if 'LSEnvironment' in content:
            print("✅ LSEnvironment already exists in Info.plist")
            return True
        
        # Add LSEnvironment before closing </dict>
        env_section = '''	<key>LSEnvironment</key>
	<dict>
		<key>LANG</key>
		<string>en_US.UTF-8</string>
		<key>LC_ALL</key>
		<string>en_US.UTF-8</string>
		<key>PYTHONIOENCODING</key>
		<string>utf-8</string>
	</dict>
</dict>'''
        
        # Replace the final </dict> with our environment + </dict>
        if content.endswith('</dict>\n</plist>'):
            content = content.replace('</dict>\n</plist>', env_section + '\n</plist>')
        elif content.endswith('</dict>\n</plist>\n'):
            content = content.replace('</dict>\n</plist>\n', env_section + '\n</plist>\n')
        else:
            print("⚠️  Unexpected Info.plist format")
            return False
        
        # Write back
        with open(plist_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Added UTF-8 environment to Info.plist")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix Info.plist: {e}")
        return False

def suggest_terminal_fix():
    """Suggest terminal encoding fix"""
    print("\n🖥️  Terminal Encoding Fix:")
    print("-" * 25)
    print("If you're still having encoding issues, try:")
    print()
    print("1. Set terminal encoding:")
    print("   export LANG=en_US.UTF-8")
    print("   export LC_ALL=en_US.UTF-8")
    print("   export PYTHONIOENCODING=utf-8")
    print()
    print("2. Add to ~/.bash_profile or ~/.zshrc:")
    print("   echo 'export LANG=en_US.UTF-8' >> ~/.bash_profile")
    print("   echo 'export LC_ALL=en_US.UTF-8' >> ~/.bash_profile")
    print("   echo 'export PYTHONIOENCODING=utf-8' >> ~/.bash_profile")
    print()
    print("3. Restart terminal and try again")

def main():
    """Main function"""
    print("🍎 WiFi Led Studio - Encoding Fix for macOS")
    print("=" * 45)
    
    # Check system encoding
    check_system_encoding()
    
    # Test Unicode output
    test_unicode_output()
    
    # Fix built app
    print("\n🔧 Fixing Built App:")
    print("-" * 18)
    
    fixes_applied = 0
    
    # Create wrapper script
    if create_encoding_wrapper():
        fixes_applied += 1
    
    # Fix Info.plist
    if fix_info_plist():
        fixes_applied += 1
    
    # Summary
    print("\n" + "=" * 45)
    print(f"Applied {fixes_applied}/2 encoding fixes")
    
    if fixes_applied > 0:
        print("🎉 Encoding fixes applied!")
        print("\nTo run the app with proper encoding:")
        print('   open "build_simple_protected/WiFi Led Studio.app"')
        print("   or use the wrapper script")
    else:
        print("⚠️  No fixes could be applied")
        suggest_terminal_fix()
    
    return fixes_applied > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)