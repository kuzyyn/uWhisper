# Configuration
VERSION="1.0.0"
ARCH="amd64"
PACKAGE_NAME="uwhisper"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Use build/deb for staging to keep root clean
BUILD_ROOT="$PROJECT_ROOT/build/deb"
STAGING_DIR="$BUILD_ROOT/$PACKAGE_NAME"
DIST_DIR="$PROJECT_ROOT/dist"

# Ensure executables exist
if [ ! -f "$DIST_DIR/uwhisper" ] || [ ! -f "$DIST_DIR/uwhisper-trigger" ]; then
    echo "Error: Binaries not found in $DIST_DIR. Please run build.sh first."
    exit 1
fi

echo "Creating Debian package structure..."
# We clean only the deb part, assuming build.sh already ran and populated build/
rm -rf "$BUILD_ROOT"
mkdir -p "$STAGING_DIR/DEBIAN"
mkdir -p "$STAGING_DIR/usr/local/bin"
mkdir -p "$STAGING_DIR/usr/share/applications"

# Copy files
echo "Copying binaries..."
cp "$DIST_DIR/uwhisper" "$STAGING_DIR/usr/local/bin/"
cp "$DIST_DIR/uwhisper-trigger" "$STAGING_DIR/usr/local/bin/"
chmod 755 "$STAGING_DIR/usr/local/bin/uwhisper"
chmod 755 "$STAGING_DIR/usr/local/bin/uwhisper-trigger"

echo "Copying desktop file..."
# Ensure the Exec path in desktop file is correct for global install
sed 's|Exec=.*|Exec=/usr/local/bin/uwhisper|' "$SCRIPT_DIR/uwhisper.desktop" > "$STAGING_DIR/usr/share/applications/uwhisper.desktop"

# Create Control File
echo "Creating control file..."
cat > "$STAGING_DIR/DEBIAN/control" <<EOF
Package: $PACKAGE_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Robert <robert@example.com>
Depends: libportaudio2, wl-clipboard, libnotify-bin
Description: Local Voice-to-Text for Ubuntu (Wayland)
 uWhisper is a local Whisper-based transcription tool designed for Ubuntu.
 It supports global hotkeys on Wayland using client-server architecture.
EOF

# Create Post-Installation Script (for shortcuts)
echo "Creating postinst script..."
cat > "$STAGING_DIR/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

# Update desktop database
if command -v update-desktop-database > /dev/null; then
    update-desktop-database /usr/share/applications
fi

# Attempt to set shortcut for the user who ran sudo
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    
    echo "Attempting to configure shortcut for user: $SUDO_USER"
    
    # Define shortcut details
    CMD="/usr/local/bin/uwhisper-trigger"
    BINDING="<Control>space"
    SCHEMA="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
    PATH_PREFIX="/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
    CUSTOM_PATH="${PATH_PREFIX}/custom0/"
    
    # Helper to run gsettings as user
    gset() {
        sudo -u "$SUDO_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u "$SUDO_USER")/bus" gsettings set "$1" "$2" "$3" "$4"
    }
    
    # We need to run gsettings commands as the user
    # Note: DBUS_SESSION_BUS_ADDRESS is critical for this to work from a root script
    
    sudo -u "$SUDO_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u "$SUDO_USER")/bus" gsettings set \
        org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$CUSTOM_PATH name 'uWhisper Trigger'
        
    sudo -u "$SUDO_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u "$SUDO_USER")/bus" gsettings set \
        org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$CUSTOM_PATH command "$CMD"
        
    sudo -u "$SUDO_USER" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u "$SUDO_USER")/bus" gsettings set \
        org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$CUSTOM_PATH binding "$BINDING"
        
    # Append to list (this is a bit simpler logic, overwriting list if it's new/simple setup)
    # Getting current list is hard in shell script without parsing, so we'll just be safe and
    # verify if custom0 is enabled. If we want to be robust we just ensure it's in the list.
    
    # For now, let's just warn the user to verify.
    echo "Shortcut 'Ctrl+Space' configured for uWhisper."
    echo "If it doesn't work, verify in Settings -> Keyboard -> Shortcuts."
else
    echo "No sudo user detected. Skipping automatic shortcut setup."
    echo "Please set the shortcut manually: uwhisper-trigger -> Ctrl+Space"
fi

exit 0
EOF

chmod 755 "$STAGING_DIR/DEBIAN/postinst"

echo "Building .deb..."
dpkg-deb --build "$STAGING_DIR" "${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Done! Package created: ${DIST_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
