# Story: Show Model Info on Overlay

**Title**: Display Model and Language Information on processing Overlay

**As a** user
**I want to** see which model and language are currently being used during transcription
**So that** I validaten my settings without opening the menu and know what to expect (e.g., speed vs. accuracy).

## Acceptance Criteria

### 1. Information Display
- [ ] during the "Processing" / "Transcribing" phase, display the active Model Name (e.g., "Parakeet", "Whisper Large").
- [ ] For Whisper models, also display the selected Language (e.g., "English", "Auto", "Japanese").
- [ ] Do NOT show this information during the "Listening" phase to keep the recording view minimal

### 2. UX / UI Design
- [ ] **Recommendation**: Use a **secondary subtitle line** below the main status text to avoid clutter.
    - **Main Text**: "Processing..." (Large, Bold)
    - **Sub Text**: "Whisper Large • Japanese" (Smaller, Lighter color/opacity)

### 3. Implementation
- [ ] Pass the current model execution context (backend, model size, language) to the `OverlayWindow` when state changes to `transcribing`.
- [ ] Update `OverlayWindow.set_state` to accept an optional `details` or `subtext` argument.
- [ ] visual polish: Ensure the text fits within the overlay window and contrasts well with the background.

## UX Analysis

**Option B: Secondary Line (Recommended)**
- *Format*:
  **Processing...**
  <small>Parakeet • Fast English</small>
- *Pros*: Clear hierarchy. Keeps the primary status ("Processing") instantly readable. Looks more professional.
- *Cons*: Requires adding a second `QLabel` to the overlay layout.

**Selection**: Implement Option B for better readability, falling back to Option A if screen space is extremely constrained.
