# Story: Improve Application Icons

**Title**: Update Application and System Tray Icons

**As a** user
**I want to** see a distinct and professional icon for the application in my taskbar, system tray, and application menu
**So that** I can easily identify the app and it looks like a polished product rather than a generic terminal tool.

## Acceptance Criteria

### 1. Application Icon (Window & Taskbar)
- [ ] Replace the default system/terminal icon with a custom "uWhisper" logo.
- [ ] Ensure the icon is visible in the task switcher (Alt+Tab), dock/panel, and window title bar.
- [ ] **resource**: user to provide an icon file (e.g., `logo.png` or `app_icon.svg`).

### 2. System Tray Icon (Top Bar)
- [ ] Replace the current generic microphone icon in the system tray.
- [ ] The tray icon should be clear and legible at small sizes (16x16 or 24x24).
- [ ] Optional: It should indicate state (e.g., red dot for recording, normal for idle).
- [ ] **resource**: user to provide a tray-specific icon (often monochrome/symbolic works best on Linux).

### 3. Installation Integration
- [ ] Update the `.desktop` file generation or setup script to install the icon to the system icon path (e.g., `/usr/share/icons` or `~/.local/share/icons`).
- [ ] Ensure the application menu ("Start Menu") shows the correct icon.

## Implementation Guide for User (Where to find icons)

Since you don't have an icon yet, here are recommended free sources for high-quality, open-source icons:

1.  **Phosphor Icons** (phosphoricons.com): Clean, modern line icons. Great for the system tray.
2.  **Lucide** (lucide.dev): Very popular, simple open-source icon set.
3.  **Material Design Icons** (fonts.google.com/icons): Standard, recognizable Google style.
4.  **SVGRepo** (svgrepo.com): Search for "microphone", "sound wave", or "speech". Filter by "Monocolor" for tray icons.

**Action Plan**:
1.  Download a `.png` (at least 512x512) for the **App Icon**.
2.  Download a `.svg` or `.png` (small, high contrast) for the **Tray Icon**.
3.  Create an `assets/` or `icons/` folder in the project root.
4.  Place files there (e.g., `assets/icon.png`, `assets/tray_icon.png`).
5.  Update `src/gui.py` to load these specific files.
