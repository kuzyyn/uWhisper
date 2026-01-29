import socket
import sys
import config

def trigger_server():
    try:
        client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_sock.connect(config.SOCKET_PATH)
        client_sock.sendall(b"TOGGLE")
        client_sock.close()
    except FileNotFoundError:
        print("Error: Server socket not found. Is the server running?")
        sys.exit(1)
    except ConnectionRefusedError:
        print("Error: Connection refused. Is the server running?")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    trigger_server()
