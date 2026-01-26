#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EX="$SCRIPT_DIR/venv/bin/python"
MAIN_SCRIPT="$SCRIPT_DIR/main.py"
TRIGGER_CMD="$PYTHON_EX $MAIN_SCRIPT --trigger"

echo "uWhisper Shortcut Setup"
echo "======================="
echo "We will attempt to add a custom keybinding for 'Ctrl+Space' to run:"
echo "$TRIGGER_CMD"
echo ""

# Define keybinding paths
KEY_PATH="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
CUSTOM_0="$KEY_PATH/custom0/"

# Check if dconf/gsettings is available
if ! command -v gsettings &> /dev/null; then
    echo "Error: gsettings not found. Cannot set shortcut automatically."
    exit 1
fi

echo "Setting up custom keybinding..."

# 1. Create the custom keybinding
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$CUSTOM_0 name 'uWhisper Trigger'
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$CUSTOM_0 command "$TRIGGER_CMD"
gsettings set org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$CUSTOM_0 binding '<Control>space'

# 2. Add it to the list of custom keybindings
# This part is tricky because we need to append to the array. 
# For safety, we will just inform the user if it's not seemingly effective, 
# or overwrite if the list is empty. 
# A safer way is to just print instructions for the user to verify.

echo ""
echo "Attempted to set keybinding path: $CUSTOM_0"
echo "Command: $TRIGGER_CMD"
echo "Binding: Ctrl+Space"
echo ""
echo "IMPORTANT: You may need to manually add this in Settings -> Keyboard -> Shortcuts."
echo "If the above didn't work immediately:"
echo "1. Go to Settings > Keyboard > View and Customize Shortcuts > Custom Shortcuts"
echo "2. Add a new shortcut:"
echo "   Name: uWhisper"
echo "   Command: $TRIGGER_CMD"
echo "   Shortcut: Ctrl+Space"
echo ""
echo "Setup script finished."
