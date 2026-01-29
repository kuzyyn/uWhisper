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
    Go to the [Releases page](../../releases) and download:
    - `uwhisper` (The executable)
    - `uwhisper.desktop` (System menu shortcut)

2.  **Install Binary**:
    Make the file executable and move it to your system path:
    ```bash
    chmod +x uwhisper
    sudo cp uwhisper /usr/local/bin/uwhisper
    ```

3.  **Install Desktop Shortcut**:
    Enables the app to appear in your system menu:
    ```bash
    cp uwhisper.desktop ~/.local/share/applications/
    ```

4.  **Add Shortcut**:
    You need to create a custom keyboard shortcut (e.g., `Ctrl+Space`) to trigger the transcription.
    
    *   **Settings Path**: Settings -> Keyboard -> View and Customize Shortcuts -> Custom Shortcuts -> Add New.
    *   **Name**: uWhisper
    *   **Command**: `uwhisper --trigger`
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
    ./build.sh
    ```
    The executable will be created in `dist/uwhisper`. Follow steps 2 and 3 above to install it.

## Development Setup

### Python Dependencies
Install requirements into a virtual environment:
```bash
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
```

## Usage

1. **Start the Server** (Background process):
   ```bash
   ./venv/bin/python main.py --server
   ```

2. **Trigger Recording** (Client):
   ```bash
   ./venv/bin/python main.py --trigger
   ```



## Auto-Paste Setup (Optional)
To enable the application to automatically type/paste text into other applications (without using sudo), you need to configure system permissions one time.

1.  Run the setup script:
    ```bash
    ./setup_permissions.sh
    ```
2.  **Log out and Log back in** (or Reboot) your computer.
3.  In the uWhisper Settings, verify that **Output Mode** is set to **Clipboard + Auto-Paste**.

