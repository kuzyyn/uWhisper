#!/bin/bash
set -e

echo "========================================"
echo "      uWhisper Release Builder"
echo "========================================"

# Clean up previous builds
echo "[1/3] Cleaning previous builds..."
rm -rf build dist

# Build Binaries
echo "[2/3] Building executable binaries..."
./scripts/build.sh
cp scripts/uwhisper.desktop dist/

# Build Debian Package
echo "[3/3] Packaging .deb file..."
./scripts/build_deb.sh

echo "========================================"
echo "SUCCESS! Release artifacts are ready."
echo "Artifacts (Binaries & Package): dist/"
echo "========================================"
