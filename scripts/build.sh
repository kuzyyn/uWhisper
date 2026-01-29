#!/bin/bash
set -e

# Path configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PYTHON="$PROJECT_ROOT/venv/bin/python"
PYINSTALLER="$PROJECT_ROOT/venv/bin/pyinstaller"

# Check for venv
if [ ! -f "$PYINSTALLER" ]; then
    echo "Error: PyInstaller not found at $PYINSTALLER"
    echo "Please set up the virtual environment first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "Building uWhisper..."
echo "Project Root: $PROJECT_ROOT"

# Ensure we are in project root
cd "$PROJECT_ROOT"

# Run PyInstaller
# --onefile: Create a single executable
# --name: Name of the output binary
# --clean: Clean PyInstaller cache
# --hidden-import: pydbus is often missed by PyInstaller
"$PYINSTALLER" --onefile \
            --clean \
            --distpath "$PROJECT_ROOT/dist" \
            --workpath "$PROJECT_ROOT/build" \
            --specpath "$PROJECT_ROOT/build" \
            --name uwhisper \
            --hidden-import=pydbus \
            --hidden-import=PyQt6 \
            src/main.py

echo "Building uwhisper-trigger..."

# Build lightweight trigger
# We exclude heavy modules explicitly to ensure it stays small and starts fast
"$PYINSTALLER" --onefile \
            --clean \
            --distpath "$PROJECT_ROOT/dist" \
            --workpath "$PROJECT_ROOT/build" \
            --specpath "$PROJECT_ROOT/build" \
            --name uwhisper-trigger \
            --exclude-module=PyQt6 \
            --exclude-module=torch \
            --exclude-module=numpy \
            --exclude-module=faster_whisper \
            src/client.py

echo "Build complete!"
echo "Main Executable: dist/uwhisper"
echo "Trigger Executable: dist/uwhisper-trigger"
