# Story: Select Microphone

**Title**: Allow user to select input microphone

**As a** user
**I want to** select which microphone is used for voice input
**So that** I can use my preferred high-quality microphone instead of the default system device.

## Acceptance Criteria

### 1. Settings Window
- [x] Add a "Microphone" or "Input Device" dropdown to the Settings window.
- [x] Populate the dropdown with a list of available system audio input devices (e.g., "Default", "Webcam Mic", "Blue Yeti", etc.).
- [x] Display the currently selected device.
- [x] Allow users to save the selection.

### 2. Quick Access / Popup (Tray Menu)
- [x] Add a "Microphone" submenu or section to the System Tray / Quick Settings popup.
- [x] Allow quick switching of the input device from this menu without opening the full settings window.
- [x] Indicate the currently active microphone.

### 3. functionality
- [x] The application should initialize recording using the selected device index/ID.
- [x] If the selected device is disconnected, fall back to the system default and notify the user (optional but good UX).
- [x] Persist the selection in `config.json` (e.g., device name or ID).

## Technical Notes
- Use `sounddevice` or `PyAudio` (whichever is used in `src/server.py`) to list devices.
- Store the device name/index in settings.
- Update `Server.start_recording` logic to use the specified `device` index.
