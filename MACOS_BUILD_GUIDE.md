# macOS Build Guide for WiFi Led Studio

## Quick Start

### Method 1: Build with Hotkeys (Recommended)
```bash
python3 build_macos_with_hotkeys.py
```
*Automatically fixes pynput issues and includes hotkeys*

### Method 2: Minimal Build
```bash
python3 build_minimal_macos.py
```
*Minimal dependencies with hotkeys*

### Method 3: Safe Build Script
```bash
python3 build_macos_safe.py
```
*Auto-fixes common issues*

### Method 4: Manual Build
```bash
# 1. Protect source code
python3 simple_protect.py

# 2. Build
python3 setup_simple_protected.py build
```

### Method 4: Cross-Platform Script
```bash
python3 build_simple_protected_cross_platform.py
```

## Troubleshooting

### Common Errors

#### Error: "No module named 'numpy.core._methods'"
This is a known issue with cx-freeze and numpy on macOS.

#### Error: "No module named 'pystray._util.darwin'"
This is a pystray compatibility issue with cx-freeze on macOS.

#### Error: "No module named 'pynput.keyboard._darwin'"
This is a pynput compatibility issue with cx-freeze on macOS.

#### Error: "No module named 'icmplib'"
This means icmplib dependency is missing from the build.

**Quick Fix: Use Hotkeys Build (handles all dependencies)**
```bash
python3 build_macos_with_hotkeys.py
```

**Manual Fixes:**
```bash
# Fix pynput
python3 fix_pynput_macos.py

# Install missing dependencies
python3 install_dependencies_macos.py

# Check all dependencies
python3 check_dependencies_macos.py
```

**Other Solutions:**

#### Solution 1: Debug Script
```bash
python3 debug_macos_build.py
```

#### Solution 2: Update Dependencies
```bash
pip3 install --upgrade numpy cx-freeze
```

#### Solution 3: Specific Versions
```bash
pip3 install numpy==1.26.2 cx-freeze==7.2.2
```

#### Solution 4: Clean Reinstall
```bash
pip3 uninstall numpy cx-freeze
pip3 install numpy cx-freeze
```

#### Solution 5: Use PyInstaller Instead
```bash
pip3 install pyinstaller
pyinstaller mac.spec
```

### Other Common Issues

#### Missing Dependencies
```bash
pip3 install -r requirements.txt
```

#### Python Version Issues
- Ensure Python 3.8+ is installed
- Check with: `python3 --version`

#### Permission Issues
```bash
chmod +x build_simple_protected.sh
./build_simple_protected.sh
```

## Build Output

### Successful Build
```
build_simple_protected/
└── WiFi Led Studio.app/
    └── Contents/
        ├── Info.plist
        ├── MacOS/
        │   ├── WiFi Led Studio (executable)
        │   └── lib/
        │       ├── wls/ (bytecode protected)
        │       └── wls_frontend/
        └── Resources/
            └── WiFi Led Studio.icns
```

### Running the App
```bash
# Double-click in Finder, or:
open "build_simple_protected/WiFi Led Studio.app"

# Or run executable directly:
"build_simple_protected/WiFi Led Studio.app/Contents/MacOS/WiFi Led Studio"
```

## Distribution

### For Personal Use
- Copy the .app bundle to Applications folder
- Or run directly from build directory

### For Distribution
1. **Code Signing** (for distribution outside App Store):
   ```bash
   codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" "WiFi Led Studio.app"
   ```

2. **Notarization** (required for macOS 10.15+):
   ```bash
   xcrun notarytool submit "WiFi Led Studio.app" --keychain-profile "notarytool-profile" --wait
   ```

3. **Create DMG Installer**:
   ```bash
   hdiutil create -volname "WiFi Led Studio" -srcfolder "WiFi Led Studio.app" -ov -format UDZO "WiFi Led Studio.dmg"
   ```

## Advanced Configuration

### Custom Build Options
Edit `setup_simple_protected.py` to customize:
- Package inclusions/exclusions
- App bundle metadata
- Icon and resources
- Build optimization level

### Environment Variables
```bash
export MACOSX_DEPLOYMENT_TARGET=10.15  # Minimum macOS version
export ARCHFLAGS="-arch x86_64"        # Architecture
```

## Debugging

### Verbose Build Output
```bash
python3 setup_simple_protected.py build --verbose
```

### Check Dependencies
```bash
python3 debug_macos_build.py
```

### Test App Bundle
```bash
# Check bundle structure
ls -la "build_simple_protected/WiFi Led Studio.app/Contents/"

# Test executable
"build_simple_protected/WiFi Led Studio.app/Contents/MacOS/WiFi Led Studio" --help
```

## Performance Tips

1. **Use conda instead of pip** (sometimes more reliable):
   ```bash
   conda install numpy cx-freeze
   ```

2. **Virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Clean builds**:
   ```bash
   rm -rf build_simple_protected protected_source
   ```

## Known Limitations

- Some numpy modules may be excluded for compatibility
- Large bundle size due to included dependencies
- May require code signing for distribution
- First run might be slow due to bytecode loading

## Support

If you encounter issues:

1. Run the debug script: `python3 debug_macos_build.py`
2. Try the safe build script: `python3 build_macos_safe.py`
3. Check this guide for common solutions
4. Consider using PyInstaller as alternative: `pyinstaller mac.spec`

## Alternative: PyInstaller

If cx-freeze continues to have issues, you can use PyInstaller:

```bash
# Install PyInstaller
pip3 install pyinstaller

# Build with existing spec file
pyinstaller mac.spec

# Or create new spec
pyinstaller --onedir --windowed --name "WiFi Led Studio" wls/__main__.py
```

The PyInstaller build will be in `dist/WiFi Led Studio.app`.