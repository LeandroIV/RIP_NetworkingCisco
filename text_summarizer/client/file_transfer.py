# client/file_transfer.py
from typing import BinaryIO, Any
import json
from utils import serialize_client_data, deserialize_client_data

class ClientFileTransfer:
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size

    def send_to_server(self, server_socket: Any, data: Any) -> None:
        """Send data to server using chunked protocol"""
        try:
            serialized_data = serialize_client_data(data)
            total_length = len(serialized_data)
            
            # Send length header
            length_info = serialize_client_data({"length": total_length})
            server_socket.send(f"{len(length_info):<10}".encode('utf-8'))
            server_socket.send(length_info)
            
            # Send data chunks
            for i in range(0, total_length, self.chunk_size):
                chunk = serialized_data[i:i + self.chunk_size]
                server_socket.send(chunk)
                ack = server_socket.recv(2)
                if ack != b'ok':
                    raise Exception("Server acknowledgment error")
        except Exception as e:
            raise Exception(f"Client send error: {str(e)}")

    def receive_from_server(self, server_socket: Any) -> Any:
        """Receive data from server using chunked protocol"""
        try:
            # Get length header
            length_header = server_socket.recv(10).decode('utf-8').strip()
            length_info = server_socket.recv(int(length_header)).decode('utf-8')
            total_length = json.loads(length_info)["length"]
            
            # Receive data chunks
            received_data = b""
            while len(received_data) < total_length:
                chunk = server_socket.recv(min(self.chunk_size, total_length - len(received_data)))
                if not chunk:
                    raise Exception("Server connection closed prematurely")
                received_data += chunk
                server_socket.send(b'ok')
            
            return deserialize_client_data(received_data)
        except Exception as e:
            raise Exception(f"Client receive error: {str(e)}")