#!/usr/bin/env python3
"""
Diagnose why codesign is slow
"""

import os
import subprocess
import time

def count_files(directory, pattern="*"):
    """Count files in directory"""
    try:
        result = subprocess.run(f'find "{directory}" -name "{pattern}" | wc -l', 
                              shell=True, capture_output=True, text=True)
        return int(result.stdout.strip())
    except:
        return 0

def get_directory_size(directory):
    """Get directory size in MB"""
    try:
        result = subprocess.run(f'du -sm "{directory}"', 
                              shell=True, capture_output=True, text=True)
        return int(result.stdout.split()[0])
    except:
        return 0

def diagnose_app_bundle(app_path):
    """Diagnose app bundle for codesign performance"""
    
    print("🔍 App Bundle Diagnosis")
    print("=" * 50)
    print(f"App: {app_path}")
    print()
    
    if not os.path.exists(app_path):
        print(f"❌ App not found: {app_path}")
        return
    
    # Overall stats
    total_size = get_directory_size(app_path)
    print(f"📦 Total app size: {total_size} MB")
    
    # Contents breakdown
    contents_dir = os.path.join(app_path, "Contents")
    if os.path.exists(contents_dir):
        
        # MacOS directory
        macos_dir = os.path.join(contents_dir, "MacOS")
        if os.path.exists(macos_dir):
            macos_size = get_directory_size(macos_dir)
            total_files = count_files(macos_dir)
            python_files = count_files(macos_dir, "*.py")
            pyc_files = count_files(macos_dir, "*.pyc")
            so_files = count_files(macos_dir, "*.so")
            dylib_files = count_files(macos_dir, "*.dylib")
            
            print(f"🖥️  MacOS directory: {macos_size} MB")
            print(f"   📁 Total files: {total_files:,}")
            print(f"   🐍 Python files: {python_files:,}")
            print(f"   📦 .pyc files: {pyc_files:,}")
            print(f"   🔗 .so files: {so_files}")
            print(f"   📚 .dylib files: {dylib_files}")
            
            # Check for problematic directories
            hash_dirs = count_files(macos_dir, ".hash")
            pycache_dirs = count_files(macos_dir, "__pycache__")
            
            if hash_dirs > 0:
                print(f"   ⚠️  .hash directories: {hash_dirs}")
            if pycache_dirs > 0:
                print(f"   ⚠️  __pycache__ directories: {pycache_dirs}")
        
        # Resources directory
        resources_dir = os.path.join(contents_dir, "Resources")
        if os.path.exists(resources_dir):
            resources_size = get_directory_size(resources_dir)
            resources_files = count_files(resources_dir)
            
            print(f"📁 Resources directory: {resources_size} MB")
            print(f"   📄 Files: {resources_files}")
    
    print()
    
    # Performance predictions
    print("⏱️  Performance Analysis")
    print("-" * 30)
    
    if total_files > 10000:
        print("🐌 HIGH file count - codesign will be SLOW")
        print("   Recommendation: Clean up unnecessary files")
    elif total_files > 5000:
        print("⚠️  MEDIUM file count - codesign will be moderate")
    else:
        print("✅ LOW file count - codesign should be fast")
    
    if total_size > 500:
        print("🐌 LARGE app size - codesign will be SLOW")
        print("   Recommendation: Remove unused dependencies")
    elif total_size > 200:
        print("⚠️  MEDIUM app size - codesign will be moderate")
    else:
        print("✅ SMALL app size - codesign should be fast")
    
    if pyc_files > 1000:
        print("🐌 MANY .pyc files - consider removing for faster signing")
        print("   Note: Removing .pyc files may slow app startup")
    
    print()
    
    # Recommendations
    print("💡 Recommendations")
    print("-" * 20)
    
    if hash_dirs > 0 or pycache_dirs > 0:
        print("1. ✅ Run cleanup script to remove problematic files")
    
    if total_files > 5000:
        print("2. 🔄 Consider signing libraries separately first")
        print("3. 🚀 Use fast signing (no timestamp) for testing")
    
    if total_size > 200:
        print("4. 📦 Review dependencies - remove unused ones")
        print("5. 🗜️  Consider compression or optimization")
    
    print("6. 🌐 Check internet connection for timestamp server")
    print("7. ⚡ Use SSD storage for faster I/O")

def test_codesign_speed(app_path, cert_name):
    """Test different codesign methods"""
    
    print("🏃‍♂️ Codesign Speed Test")
    print("=" * 30)
    
    # Test 1: Verify only (fastest)
    print("Test 1: Verification only...")
    start = time.time()
    result = subprocess.run(f'codesign --verify "{app_path}"', 
                          shell=True, capture_output=True)
    verify_time = time.time() - start
    print(f"   ⏱️  Verify time: {verify_time:.1f}s")
    
    # Test 2: Fast signing (no timestamp)
    print("Test 2: Fast signing (no timestamp)...")
    start = time.time()
    result = subprocess.run(f'codesign --force --sign "{cert_name}" "{app_path}"', 
                          shell=True, capture_output=True)
    fast_time = time.time() - start
    print(f"   ⏱️  Fast sign time: {fast_time:.1f}s")
    
    if fast_time < 30:
        print("   ✅ Fast signing is quick!")
    elif fast_time < 120:
        print("   ⚠️  Fast signing is moderate")
    else:
        print("   🐌 Fast signing is slow")
    
    print()
    print("💡 If fast signing is slow, the issue is likely:")
    print("   - Too many files to sign")
    print("   - Large file sizes")
    print("   - Slow disk I/O")
    print()
    print("   If fast signing is quick but full signing is slow:")
    print("   - Network issues (timestamp server)")
    print("   - Runtime hardening checks")

if __name__ == "__main__":
    APP_PATH = "/Users/phamtuantrung/make setup/WiFi Led Studio.app"
    CERT_NAME = "Developer ID Application: Pham Tuan Trung (P6B7T335D8)"
    
    diagnose_app_bundle(APP_PATH)
    print()
    test_codesign_speed(APP_PATH, CERT_NAME)