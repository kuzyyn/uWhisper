# Story: Microphone Test

**Title**: Allow user to test microphone input

**As a** user
**I want to** record a short audio clip and have it played back to me
**So that** I can verify that my microphone is working correctly and the volume levels are appropriate.

## Acceptance Criteria

### 1. Test Interface
- [x] Add a "Test Microphone" section or button in the Settings window (e.g., near the microphone selection).
- [x] The interface should have a simple "Start Test" / "Stop Test" toggle button.

### 2. Recording & Playback Behavior
- [x] **Start Recording**: clicking "Start Test" begins recording audio from the selected microphone.
- [x] **Overlay**: During the test recording, the application MUST display the same overlay visualization (amplitude/wave) used for transcription recording to provide visual feedback.
- [x] **Stop Recording**: clicking "Stop Test" stops the recording.
- [x] **Auto-Playback**: Immediately after stopping, the recorded audio clip should automatically play back through the default system output (speakers).

### 3. Technical Implementation
- [x] Reuse the existing `OverlayWindow` for visual feedback.
- [x] Temporarily buffer audio in memory or a temporary file.
- [x] Use a standard audio playback library (e.g., `sounddevice`, `pydub`, or `playsound`) to play the clip.
- [x] Ensure the test does not trigger transcription or API calls.
