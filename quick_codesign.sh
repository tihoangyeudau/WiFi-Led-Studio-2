#!/bin/bash

# Quick codesign script for testing
# Usage: ./quick_codesign.sh

APP_PATH="/Users/phamtuantrung/make setup/WiFi Led Studio.app"
CERT_NAME="Developer ID Application: Pham Tuan Trung (P6B7T335D8)"
ENTITLEMENTS="/Users/phamtuantrung/make setup/entitlements.xml"

echo "🚀 Quick Codesign Test"
echo "======================"

# Method 1: Fast signing (no timestamp, no runtime)
echo "🏃‍♂️ Method 1: Fast signing (no network required)..."
time codesign --deep --force --verify --verbose \
              --sign "$CERT_NAME" \
              "$APP_PATH"

if [ $? -eq 0 ]; then
    echo "✅ Fast signing successful!"
    
    # Verify signature
    echo "🔍 Verifying signature..."
    codesign --verify --verbose=2 "$APP_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ Signature valid!"
        echo "🎉 Quick codesign completed!"
        exit 0
    fi
fi

echo "⚠️  Fast signing failed, trying full signing..."

# Method 2: Full signing (with timestamp and runtime)
echo "🐌 Method 2: Full signing (requires network)..."
time codesign --deep --force --verify --verbose --timestamp \
              --options runtime \
              --entitlements "$ENTITLEMENTS" \
              --sign "$CERT_NAME" \
              "$APP_PATH"

if [ $? -eq 0 ]; then
    echo "✅ Full signing successful!"
    
    # Verify signature
    echo "🔍 Verifying signature..."
    codesign --verify --verbose=2 "$APP_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ Signature valid!"
        echo "🎉 Full codesign completed!"
    else
        echo "❌ Signature verification failed"
        exit 1
    fi
else
    echo "❌ Full signing failed"
    exit 1
fi