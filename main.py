import argparse
import sys
import os
import threading
import time
import socket

# Ensure we can find our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config_manager import settings

def is_server_running():
    socket_path = "/tmp/uwhisper.sock"
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
        import server
        s = server.WhisperServer()
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