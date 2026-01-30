import argparse
import sys
import os
import threading
import time
import socket

# Ensure we can find our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from config_manager import settings
from config import SOCKET_PATH

def setup_logging():
    if not settings.get("enable_logging", True):
        return

    log_dir = settings.get("log_dir", "/tmp/uwhisper_logs")
    if not log_dir:
        log_dir = "/tmp/uwhisper_logs"

    try:
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "uwhisper.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info(f"Logging initialized. Writing to {log_file}")
    except Exception as e:
        print(f"Failed to setup logging: {e}")


def is_server_running():
    socket_path = SOCKET_PATH
    if not os.path.exists(socket_path):
        return False
    try:
        # Try to connect to check if it's really alive
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(socket_path)
        sock.close()
        return True
    except ConnectionRefusedError:
        # Socket file exists but no one is listening (stale)
        try:
            os.remove(socket_path)
        except:
            pass
        return False
    except Exception:
        return False

def start_background_server():
    import server
    s = server.WhisperServer()
    # We run the server loop in a separate thread so GUI can run in main
    t = threading.Thread(target=s.start, daemon=True)
    t.start()
    return s

def main():
    parser = argparse.ArgumentParser(description="uWhisper: Local Voice-to-Text")
    parser.add_argument("--server", action="store_true", help="Start the uWhisper background server (headless)")
    parser.add_argument("--gui", action="store_true", help="Start with GUI and System Tray")
    parser.add_argument("--trigger", action="store_true", help="Trigger recording/transcription (Client)")
    
    args = parser.parse_args()
    
    setup_logging()

    if args.trigger:
        import client
        client.trigger_server()
        return

    # Check if already running before starting Server or GUI
    if is_server_running():
        print("uWhisper is already running!")
        # Optional: Send a signal to open settings?
        # For now, just exit to prevent duplicate instances/icons
        sys.exit(0)

    if args.server:
        # Headless mode
        logging.info("Starting in HEADLESS server mode (No GUI/Icon).")
        logging.info("Run without --server (or with --gui) to see the System Tray Icon and Settings.")
        import server
        s = server.WhisperServer()
        s.headless = True
        s.start()
        return

    # Default to GUI if no args or --gui (and not triggered)
    import gui
    
    # Start server in background thread
    server_instance = start_background_server()
    
    # Start GUI application (this blocks until quit)
    # Pass server methods for graceful shutdown AND server instance for signals
    app = gui.SystemTrayApp(None, server_instance.stop, server_instance=server_instance)
    app.run()

if __name__ == "__main__":
    main()