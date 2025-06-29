#!/usr/bin/env python3
"""
Optimize codesign process for faster signing
"""

import os
import subprocess
import time

def run_command(cmd, description):
    """Run command and measure time"""
    print(f"🔄 {description}...")
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} completed in {elapsed:.1f}s")
            return True
        else:
            print(f"❌ {description} failed in {elapsed:.1f}s")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ {description} error in {elapsed:.1f}s: {e}")
        return False

def optimize_codesign(app_path, cert_name, entitlements_path):
    """Optimized codesign process"""
    
    print("🚀 Optimized Codesign Process")
    print("=" * 50)
    
    # Step 1: Sign libraries first (parallel-friendly)
    lib_path = os.path.join(app_path, "Contents/MacOS/lib")
    if os.path.exists(lib_path):
        print("📚 Step 1: Signing libraries...")
        
        # Find and sign .so files (native libraries)
        so_files_cmd = f'find "{lib_path}" -name "*.so" -exec codesign --force --sign "{cert_name}" {{}} \\;'
        run_command(so_files_cmd, "Signing .so files")
        
        # Find and sign .dylib files (dynamic libraries)  
        dylib_files_cmd = f'find "{lib_path}" -name "*.dylib" -exec codesign --force --sign "{cert_name}" {{}} \\;'
        run_command(dylib_files_cmd, "Signing .dylib files")
    
    # Step 2: Sign main executable
    executable_path = os.path.join(app_path, "Contents/MacOS/WiFi Led Studio")
    if os.path.exists(executable_path):
        exec_cmd = f'codesign --force --sign "{cert_name}" "{executable_path}"'
        run_command(exec_cmd, "Signing main executable")
    
    # Step 3: Sign app bundle (final step)
    print("📦 Step 3: Final app bundle signing...")
    
    # Option A: Fast signing (no timestamp, no runtime)
    fast_cmd = f'''codesign --deep --force --verify --verbose \\
                  --sign "{cert_name}" \\
                  "{app_path}"'''
    
    print("🏃‍♂️ Trying fast signing first...")
    if run_command(fast_cmd, "Fast codesign"):
        print("✅ Fast signing successful!")
        return True
    
    # Option B: Full signing (with timestamp and runtime)
    print("🐌 Fast signing failed, trying full signing...")
    full_cmd = f'''codesign --deep --force --verify --verbose --timestamp \\
                  --options runtime \\
                  --entitlements "{entitlements_path}" \\
                  --sign "{cert_name}" \\
                  "{app_path}"'''
    
    return run_command(full_cmd, "Full codesign with runtime")

def check_signature(app_path):
    """Verify signature"""
    print("🔍 Verifying signature...")
    
    # Basic verification
    verify_cmd = f'codesign --verify --verbose=2 "{app_path}"'
    if run_command(verify_cmd, "Signature verification"):
        
        # Display signature info
        info_cmd = f'codesign --display --verbose=2 "{app_path}"'
        run_command(info_cmd, "Signature info")
        
        return True
    
    return False

if __name__ == "__main__":
    # Configuration
    APP_PATH = "/Users/phamtuantrung/make setup/WiFi Led Studio.app"
    CERT_NAME = "Developer ID Application: Pham Tuan Trung (P6B7T335D8)"
    ENTITLEMENTS_PATH = "/Users/phamtuantrung/make setup/entitlements.xml"
    
    print("🔐 macOS App Codesign Optimizer")
    print("=" * 50)
    print(f"App: {APP_PATH}")
    print(f"Certificate: {CERT_NAME}")
    print(f"Entitlements: {ENTITLEMENTS_PATH}")
    print()
    
    # Check if app exists
    if not os.path.exists(APP_PATH):
        print(f"❌ App not found: {APP_PATH}")
        exit(1)
    
    # Check if entitlements exist
    if not os.path.exists(ENTITLEMENTS_PATH):
        print(f"❌ Entitlements not found: {ENTITLEMENTS_PATH}")
        exit(1)
    
    # Run optimized codesign
    start_total = time.time()
    
    if optimize_codesign(APP_PATH, CERT_NAME, ENTITLEMENTS_PATH):
        if check_signature(APP_PATH):
            total_time = time.time() - start_total
            print()
            print("🎉 Codesign completed successfully!")
            print(f"⏱️  Total time: {total_time:.1f}s")
        else:
            print("❌ Signature verification failed")
    else:
        print("❌ Codesign failed")