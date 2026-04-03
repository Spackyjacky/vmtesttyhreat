#!/usr/bin/env python3
"""
ThreatPad Executable Builder
Creates standalone executable using PyInstaller
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """Install PyInstaller if not present"""
    try:
        import PyInstaller
        print("✓ PyInstaller already installed")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            print("✓ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install PyInstaller: {e}")
            return False

def build_executable():
    """Build the executable using PyInstaller"""
    
    # PyInstaller command options
    cmd = [
        "pyinstaller",
        "--onefile",                    # Single executable file
        "--windowed",                   # No console window (GUI app)
        "--name=ThreatPad",            # Executable name
        "--icon=threatpad.ico",        # Icon (if exists)
        "--add-data=templates:templates",  # Include templates folder
        "--hidden-import=tkinterdnd2", # Ensure drag-drop is included
        "--hidden-import=ascii_menu",  # Ensure ASCII Quick Menu is included
        "--clean",                     # Clean build
        "threatpad.py"
    ]
    
    # Remove icon option if no icon file exists
    if not os.path.exists("threatpad.ico"):
        cmd.remove("--icon=threatpad.ico")
        print("Note: No icon file found, building without custom icon")
    
    # Remove templates if folder doesn't exist
    if not os.path.exists("templates"):
        cmd.remove("--add-data=templates:templates")
        print("Note: No templates folder found")
    
    print("Building executable...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.check_call(cmd)
        print("✓ Build completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Build failed: {e}")
        return False

def cleanup_build_files():
    """Clean up build artifacts"""
    cleanup_dirs = ["build", "__pycache__"]
    cleanup_files = ["ThreatPad.spec"]
    
    for dir_name in cleanup_dirs:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"✓ Cleaned up {dir_name}/")
    
    for file_name in cleanup_files:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"✓ Cleaned up {file_name}")

def main():
    """Main build process"""
    print("=" * 50)
    print("ThreatPad Executable Builder")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("threatpad.py"):
        print("✗ Error: threatpad.py not found in current directory")
        sys.exit(1)
    
    # Install PyInstaller
    if not install_pyinstaller():
        sys.exit(1)
    
    # Build executable
    if build_executable():
        print("\n" + "=" * 50)
        print("BUILD SUCCESSFUL!")
        print("=" * 50)
        print(f"Executable created: dist/ThreatPad{'exe' if sys.platform == 'win32' else ''}")
        print("\nNext steps:")
        print("1. Test the executable in dist/ folder")
        print("2. For Windows deployment, copy to Windows machine")
        print("3. The executable is standalone - no Python installation needed")
        
        # Show file size
        exe_path = Path("dist") / ("ThreatPad.exe" if sys.platform == 'win32' else "ThreatPad")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"4. File size: {size_mb:.1f} MB")
    else:
        print("\n" + "=" * 50)
        print("BUILD FAILED!")
        print("=" * 50)
        sys.exit(1)
    
    # Ask about cleanup
    response = input("\nClean up build files? (y/N): ").lower()
    if response == 'y':
        cleanup_build_files()

if __name__ == "__main__":
    main()