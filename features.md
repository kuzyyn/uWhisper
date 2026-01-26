# uWhisper Feature Roadmap

## Strategy
**Current Status:** Phase 2 (GUI & Basic Config) is COMPLETE. Auto-Paste is COMPLETE.
**Next Focus:** Visual Polish (Overlay) and Model Management.

---

## Features

### 1. Configuration & UI [COMPLETED]
- [x] Create `SettingsManager` class to load/save `config.json`.
- [x] Implement a System Tray Icon.
### 1. Configuration & UI [COMPLETED]
- [x] Create `SettingsManager` class to load/save `config.json`.
- [x] Implement a System Tray Icon.
- [x] Implement a Settings Window (PyQt6).
- [x] **[NEW] Notification Toggle**: Checkbox to disable `notify-send` system bubbles.

### 2. Model Selection [PARTIAL]
**Goal:** Allow user to balance speed vs. accuracy.
- [x] Add `Model Selection` dropdown to GUI.
- [ ] **[NEW] Model Management UI**:
    - [ ] **Confirmation**: When changing model, Button "Download & Switch".
    - [ ] **Progress**: Show download progress bar in GUI.
    - [ ] **Management**: List installed models with a "Delete" (trash icon) button.
    - [ ] **Lazy Loading**: Only load when needed (optional optimization).

### 3. Language Control [COMPLETED]
- [x] Add `Language` dropdown to GUI.
- [x] Pass language parameter dynamically.

### 4. Robust Trigger (Debounce) [COMPLETED]
**Goal:** Prevent accidental double-toggles from holding the shortcut.
**Plan:**
- [x] **Debounce Logic**: Ignore `TOGGLE` commands if received within 500ms of the last one.
- [ ] **State Locking**: Lock the state during transitions.

### 5. Output Modes & Auto-Paste [COMPLETED]
**Goal:** Auto-Paste securely on Wayland.
- [x] **Mode A: Clipboard Only**.
- [x] **Mode B: Auto-Paste (Native)**: Implemented using `evdev` + udev rules.
- [x] **Mode C: Direct Input**: (Solved by Mode B).

### 5. [NEW] Visual Overlay & Animation
**Goal:** Make the app beautiful and responsive.
**Plan:**
- [ ] **Overlay Window**: A frameless, always-on-top window appearing at the bottom center.
- [ ] **Content**:
    - **Icon**: The chosen icon (App logo or Mode icon).
    - **Animation**: A real-time waveform or bar visualizer reacting to microphone amplitude.
    - **Meta Info**: Show selected Language (Flag?) and Mode (Clipboard/Paste).
- [ ] **Behavior**:
    - Appears immediately on "Start Recording".
    - Animates while speaking.
    - Shows "Transcribing..." spinner on stop.
    - Disappears automatically after success notification.

### 6. Packaging (Ubuntu Executable)
**Goal:** Easy install without terminal venv dancing.
**Plan:**
- [ ] Use `PyInstaller` to bundle everything into a single binary (`uwhisper`).
- [ ] Create a `.desktop` file for system menu integration.
