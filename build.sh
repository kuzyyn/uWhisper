#!/bin/bash
set -e

echo "Building uWhisper..."

# install requirements if needed (optional check)
# pip install -r requirements.txt

# Clean previous builds
rm -rf build dist

# Run PyInstaller
# --onefile: Create a single executable
# --name: Name of the output binary
# --clean: Clean PyInstaller cache
# --windowed: Do not open a console window (since it's a GUI app, though it has CLI args)
# --add-data: Add necessary data files if any (none for now based on analysis)
# --hidden-import: pydbus is often missed by PyInstaller
pyinstaller --onefile \
            --clean \
            --name uwhisper \
            --hidden-import=pydbus \
            --hidden-import=PyQt6 \
            main.py

echo "Build complete! Executable is in dist/uwhisper"
