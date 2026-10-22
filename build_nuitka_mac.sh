#!/bin/bash
# Build "WiFi Led Studio.app" with Nuitka (standalone) on macOS.
#
#   ./build_nuitka_mac.sh            build only
#   SIGN_ID="<identity hash or name>" ./build_nuitka_mac.sh   build and sign
#
# Run it from an environment that has the project installed (pip install .)
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python}"
OUT_DIR="dist_nuitka"
APP_NAME="WiFi Led Studio"
BUNDLE_ID="com.rml.wifiledstudio"

"$PYTHON" -m pip install -q nuitka ordered-set zstandard

"$PYTHON" -m nuitka \
    --standalone \
    --assume-yes-for-downloads \
    --output-dir="$OUT_DIR" \
    --output-filename="$APP_NAME" \
    --macos-create-app-bundle \
    --macos-app-name="$APP_NAME" \
    --macos-app-icon="icons/WiFi Led Studio.icns" \
    --macos-signed-app-name="$BUNDLE_ID" \
    --macos-app-mode=background \
    --macos-app-protected-resource="NSMicrophoneUsageDescription:WiFi Led Studio needs microphone access to capture audio for light effects and visualizations" \
    --macos-app-protected-resource="NSAppleEventsUsageDescription:WiFi Led Studio needs to control other applications to synchronize light effects with media playback" \
    --macos-app-protected-resource="NSLocalNetworkUsageDescription:WiFi Led Studio needs to discover and control WiFi lighting devices on your local network" \
    --macos-app-protected-resource="NSCameraUsageDescription:WiFi Led Studio does not use the camera, but the audio framework may require this permission" \
    --include-package=wls \
    --include-package=wls_frontend \
    --include-package=pynput \
    --include-package=pystray \
    --include-package=sentry_sdk \
    --noinclude-dlls="*.dll" \
    --include-package-data=wls \
    --include-package-data=bokeh \
    --include-package-data=xyzservices \
    --include-data-dir=wls_frontend=wls_frontend \
    --include-data-dir=icons=icons \
    --include-data-files=icons/tray.png=tray.png \
    wls/__main__.py

APP="$OUT_DIR/__main__.app"
[ -d "$APP" ] || APP="$(find "$OUT_DIR" -maxdepth 1 -name '*.app' | head -n 1)"
FINAL="$OUT_DIR/$APP_NAME.app"
if [ "$APP" != "$FINAL" ]; then
    rm -rf "$FINAL"
    mv "$APP" "$FINAL"
fi

PLIST="$FINAL/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :NSBonjourServices" "$PLIST" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :NSBonjourServices array" "$PLIST"
i=0
for service in _http._tcp _tcp _udp _rml._tcp _services._dns-sd._udp; do
    /usr/libexec/PlistBuddy -c "Add :NSBonjourServices:$i string $service" "$PLIST"
    i=$((i + 1))
done
/usr/libexec/PlistBuddy -c "Set :CFBundleIdentifier $BUNDLE_ID" "$PLIST"

# Nuitka links against the newest SDK, and with it macOS stops drawing the
# images of menu items. Report SDK 11.0 like PyInstaller does. This voids the
# signature, so it has to happen before signing.
EXE="$FINAL/Contents/MacOS/$APP_NAME"
vtool -set-build-version macos 11.0 11.0 -replace -output "$EXE.tmp" "$EXE"
mv "$EXE.tmp" "$EXE"
chmod +x "$EXE"
codesign --force --sign - "$EXE"

if [ -n "${SIGN_ID:-}" ]; then
    # Sign nested binaries first, then the bundle
    find "$FINAL" -type f \( -name "*.so" -o -name "*.dylib" -o -perm +111 \) -print0 |
        while IFS= read -r -d '' f; do
            if file "$f" | grep -q "Mach-O"; then
                codesign --force --options runtime --timestamp --sign "$SIGN_ID" "$f"
            fi
        done
    codesign --force --options runtime --timestamp \
        --entitlements entitlements.xml --sign "$SIGN_ID" "$FINAL"
    codesign --verify --deep --strict "$FINAL"
fi

echo "Built: $FINAL"
