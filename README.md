# uWhisper

uWhisper is a local Voice-to-Text application for Ubuntu, designed to work around Wayland restrictions. It uses a Client-Server architecture to provide global hotkey support for transcription.

## Features
- **Local Processing**: Uses `faster-whisper` on CPU.
- **Wayland Compatible**: Uses `wl-copy` for clipboard integration.
- **Global Shortcut**: Default `Ctrl+Space` (via GNOME Custom Shortcuts).
- **Notifications**: System notifications for status updates.

## System Requirements

Before installing, ensure you have the necessary system utilities:
```bash
sudo apt-get update
sudo apt-get install -y libportaudio2 wl-copy libnotify-bin
```
* `libportaudio2`: Required for microphone access.
* `wl-copy`: Required for clipboard operations on Wayland.
* `libnotify-bin`: Required for showing notifications.

## Installation

The easiest way to install uWhisper is to download the latest release.

1.  **Download**:
    Go to the [Releases page](../../releases) and download `uwhisper_1.0.0_amd64.deb`.

2.  **Install**:
    Run the following command to install the application, dependencies, and set up the shortcut automatically:
    ```bash
    sudo dpkg -i uwhisper_1.0.0_amd64.deb
    sudo apt --fix-broken install  # Run this if there are any dependency errors
    ```

3.  **Verify Shortcut**:
    The installation attempts to set `Ctrl+Space` as the global shortcut. Try pressing it!
    *   If it doesn't work, go to **Settings -> Keyboard -> Shortcuts** and add it manually:
        *   **Command**: `uwhisper-trigger`
        *   **Shortcut**: `Ctrl+Space`

### Manual Installation (Advanced)
If you prefer not to use the `.deb` file, you can install the binaries manually.

1.  **Download**:
    Download `uwhisper`, `uwhisper-trigger`, and `uwhisper.desktop` from releases.

2.  **Install Binaries**:
    ```bash
    chmod +x uwhisper uwhisper-trigger
    sudo cp uwhisper /usr/local/bin/uwhisper
    sudo cp uwhisper-trigger /usr/local/bin/uwhisper-trigger
    ```

3.  **Install Desktop Shortcut**:
    ```bash
    cp uwhisper.desktop ~/.local/share/applications/
    ```

4.  **Add Shortcut**:
    You need to create a custom keyboard shortcut (e.g., `Ctrl+Space`) to trigger the transcription.
    
    *   **Settings Path**: Settings -> Keyboard -> View and Customize Shortcuts -> Custom Shortcuts -> Add New.
    *   **Name**: uWhisper
    *   **Command**: `uwhisper-trigger`
    *   **Shortcut**: `Ctrl+Space` (or your preferred key)

    *Alternatively, if you downloaded the source or `setup_shortcut.sh`, you can run it to attempt automatic configuration.*

## Building from Source

If you prefer to build the executable yourself:

1.  **Set up Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2.  **Build**:
    ```bash
    ./build_release.sh
    ```
    The executables will be created in `dist/`:
    - `dist/uwhisper` (Main App)
    - `dist/uwhisper-trigger` (Shortcut Trigger)
    - `dist/uwhisper.desktop` (System Menu Integration)
    
    Follow steps 2 and 3 above to install them.
    
    *Alternatively, you can build the .deb package yourself:*
    ```bash
    ./build_release.sh
    ```
    The `.deb` file will be created in `dist/`.

## Development Setup

### Python Dependencies
Install requirements into a virtual environment:
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Usage
    
1. **Start the Application** (GUI + Tray Icon):
   ```bash
   ./venv/bin/python src/main.py
   ```
   *This will show the microphone icon in your system tray where you can access Settings.*

2. **Trigger Recording** (Global Shortcut):
   
   Once the app is running, press your configured shortcut (e.g., `Ctrl+Space`) to toggle recording.
   
   *Alternatively, you can trigger it manually:*
   ```bash
   ./venv/bin/python main.py --trigger
   ```

3. **Headless Server** (Advanced):
   
   If you want to run without the GUI (e.g., as a background service):
   ```bash
   ./venv/bin/python src/main.py --server
   ```


## Auto-Paste Setup (Optional)
To enable the application to automatically type/paste text into other applications (without using sudo), you need to configure system permissions one time.

1.  Run the setup script:
    ```bash
    ./setup_permissions.sh
    ```
2.  **Log out and Log back in** (or Reboot) your computer.
3.  In the uWhisper Settings, verify that **Output Mode** is set to **Clipboard + Auto-Paste**.

