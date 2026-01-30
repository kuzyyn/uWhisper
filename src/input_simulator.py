
import logging
import time

def simulate_ctrl_v():
    """Simulates Ctrl+V using evdev. Returns True on success."""
    try:
        from evdev import UInput, ecodes
        # Create a virtual keyboard
        with UInput() as ui:
            # Press Ctrl
            ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
            # Press V
            ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
            # Sync
            ui.syn()
            
            time.sleep(0.05)
            
            # Release V
            ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
            # Release Ctrl
            ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
            ui.syn()
            
        logging.info("Simulated Ctrl+V (evdev)")
        return True
    except ImportError:
        logging.warning("evdev module not found.")
    except Exception as e:
        logging.error(f"evdev failed: {e}")
    return False
