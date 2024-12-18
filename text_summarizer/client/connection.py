# client/connection.py
import socket
from utils import format_error

class ClientConnection:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self._socket = None

    def create_socket(self, timeout=30):
        """Create client socket with timeout"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            return self._socket
        except Exception as e:
            raise Exception(f"Failed to create client socket: {format_error(e)}")

    def connect_to_server(self):
        """Connect to server"""
        try:
            self._socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            raise Exception("Server is not running or connection was refused")
        except Exception as e:
            raise Exception(f"Failed to connect to server: {format_error(e)}")

    def close(self):
        """Close client socket"""
        if self._socket:
            self._socket.close()
            self._socket = None