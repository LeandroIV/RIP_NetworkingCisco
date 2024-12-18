# connection.py
import socket
from utils import format_error

class ServerConnection:
    def __init__(self, host='127.0.0.1', port=65432):
        self.host = host
        self.port = port
        self._socket = None

    def create_socket(self):
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Add socket reuse option to prevent "Address already in use" errors
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.host, self.port))
            self._socket.listen(5)
            print(f"Socket created, listening on {self.host}:{self.port}")
            return self._socket
        except Exception as e:
            print(f"Error creating socket: {e}")
            raise Exception(f"Failed to create server socket: {format_error(e)}")

    def accept_client(self):
        if not self._socket:
            raise Exception("Socket not initialized")
        try:
            print("Waiting for a client...")
            client_socket, address = self._socket.accept()
            print(f"Client connected from {address}")
            return client_socket, address
        except Exception as e:
            print(f"Error accepting client: {e}")
            raise Exception(f"Failed to accept client: {format_error(e)}")

    def close(self):
        """Close server socket"""
        if self._socket:
            try:
                self._socket.close()
                print("Server socket closed")
            except Exception as e:
                print(f"Error closing socket: {e}")
            finally:
                self._socket = None