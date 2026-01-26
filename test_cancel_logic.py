import sys
import threading
import time
import queue
from unittest.mock import MagicMock, patch

# Mock sounddevice to avoid hardware dependency during test
sys.modules['sounddevice'] = MagicMock()
# Mock faster_whisper to avoid model loading
sys.modules['faster_whisper'] = MagicMock()

import server

def test_cancellation_logic():
    print("Testing Cancellation Logic...")
    s = server.WhisperServer()
    
    # Mock signals
    s.signals = MagicMock()
    
    # 1. Start Recording
    print("\n--- Test 1: Start/Cancel Recording ---")
    s.recording = True
    s.audio_queue.put(b'fake_audio')
    print(f"State: recording={s.recording}, queue_size={s.audio_queue.qsize()}")
    
    # Cancel
    print("Cancelling...")
    s.cancel_recording()
    
    assert s.recording == False, "Recording should be False"
    assert s.abort_transcription == True, "Abort flag should be True"
    assert s.audio_queue.empty(), "Queue should be empty"
    s.signals.state_changed.emit.assert_called_with("idle")
    print("✅ Cancel Recording: PASSED")

    # 2. Test Abort during Transcription
    print("\n--- Test 2: Abort during Process Audio ---")
    s.abort_transcription = True
    
    # Run process_audio directly
    s.process_audio()
    
    # Verify it emitted idle immediately and didn't crash
    s.signals.state_changed.emit.assert_called_with("idle")
    assert s.abort_transcription == False, "Abort flag should be reset to False after processing"
    print("✅ Abort Transcription: PASSED")
    
    # 3. Test Reset on New Recording
    print("\n--- Test 3: Reset on New Start ---")
    # Simulate valid connection for handle_client
    mock_conn = MagicMock()
    mock_conn.recv.return_value = b"TOGGLE"
    
    # Force some time diff
    s.last_toggle_time = 0 
    
    # We need to ensure recording is currently False so it starts
    s.recording = False
    
    s.handle_client(mock_conn)
    
    assert s.recording == True, "Should be recording"
    assert s.abort_transcription == False, "Abort flag should be reset to False"
    print("✅ Reset on Start: PASSED")

if __name__ == "__main__":
    try:
        test_cancellation_logic()
        print("\n🎉 ALL TESTS PASSED")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)
