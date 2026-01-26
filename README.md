# uWhisper

uWhisper is a local Voice-to-Text application for Ubuntu, designed to work around Wayland restrictions. It uses a Client-Server architecture to provide global hotkey support for transcription.

## Features
- **Local Processing**: Uses `faster-whisper` on CPU.
- **Wayland Compatible**: Uses `wl-copy` for clipboard integration.
- **Global Shortcut**: Default `Ctrl+Space` (via GNOME Custom Shortcuts).
- **Notifications**: System notifications for status updates.

## Requirements

### System Dependencies
You need to install the following system packages:
```bash
sudo apt-get update
sudo apt-get install -y libportaudio2 wl-copy libnotify-bin
```
* `libportaudio2`: Required for microphone access (`sounddevice`).
* `wl-copy`: Required for clipboard operations on Wayland.
* `libnotify-bin`: Required for `notify-send`.

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

3. **Setup Shortcut**:
   Run the provided script to attempt automatic configuration:
   ```bash
   ./setup_shortcut.sh
   ```
   Or manually add a custom shortcut in GNOME Settings pointing to the trigger command.

## Auto-Paste Setup (Optional)
To enable the application to automatically type/paste text into other applications (without using sudo), you need to configure system permissions one time.

1.  Run the setup script:
    ```bash
    ./setup_permissions.sh
    ```
2.  **Log out and Log back in** (or Reboot) your computer.
3.  In the uWhisper Settings, verify that **Output Mode** is set to **Clipboard + Auto-Paste**.

