#!/usr/bin/env python3
"""
Simple source protection - just compile to bytecode without obfuscation
"""

import os
import shutil
import py_compile
from pathlib import Path

def compile_directory(source_dir, output_dir):
    """Compile Python files to .pyc"""
    print(f"Compiling {source_dir} to {output_dir}...")

    for root, dirs, files in os.walk(source_dir):
        # Skip __pycache__ directories
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')
            
        for file in files:
            if file.endswith('.py'):
                source_path = os.path.join(root, file)
                rel_path = os.path.relpath(source_path, source_dir)

                # Create output directory structure
                output_file_dir = os.path.join(output_dir, os.path.dirname(rel_path))
                os.makedirs(output_file_dir, exist_ok=True)

                # For __main__.py, we need to keep both .py and .pyc
                if file == '__main__.py':
                    # Copy the original .py file (needed for PyInstaller entry point)
                    shutil.copy2(source_path, os.path.join(output_file_dir, file))
                    print(f"  📄 {rel_path} (kept as .py for entry point)")
                
                # Compile to .pyc
                pyc_path = os.path.join(output_file_dir, file + 'c')
                try:
                    py_compile.compile(source_path, pyc_path, doraise=True)
                    print(f"  ✓ {rel_path} → {file}c")
                except Exception as e:
                    print(f"  ✗ {rel_path}: {e}")
                    # Fallback: copy source file
                    if file != '__main__.py':  # Don't duplicate __main__.py
                        shutil.copy2(source_path, os.path.join(output_file_dir, file))
            else:
                # Copy non-Python files
                source_path = os.path.join(root, file)
                rel_path = os.path.relpath(source_path, source_dir)
                output_path = os.path.join(output_dir, rel_path)
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                shutil.copy2(source_path, output_path)
                print(f"  📁 {rel_path}")

def protect_source():
    """Simple source protection"""
    print("🔐 Simple Source Protection")
    print("===========================")
    print()

    # Create protected directories
    protected_dir = "protected_source"
    if os.path.exists(protected_dir):
        shutil.rmtree(protected_dir)

    os.makedirs(protected_dir, exist_ok=True)

    # Compile wls directory
    print("🔒 Compiling wls directory...")
    compile_directory("wls", os.path.join(protected_dir, "wls"))

    # Copy wls_frontend (static files)
    print("📁 Copying wls_frontend...")
    shutil.copytree("wls_frontend", os.path.join(protected_dir, "wls_frontend"))

    print("✅ Simple protection completed!")
    print(f"📂 Protected source: {protected_dir}")

    return protected_dir

if __name__ == "__main__":
    protect_source()