#!/bin/bash
# Simple build script for ThreatPad

echo "Building ThreatPad executable..."

# Install PyInstaller if needed
python3 -m pip install pyinstaller

# Build the executable
pyinstaller --onefile --windowed --name=ThreatPad --clean threatpad.py

# Check if build was successful
if [ -f "dist/ThreatPad" ]; then
    echo "✓ Build successful! Executable created: dist/ThreatPad"
    ls -lh dist/ThreatPad
else
    echo "✗ Build failed!"
    exit 1
fi