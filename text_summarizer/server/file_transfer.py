# file_transfer.py
from typing import BinaryIO, Any
import json
from utils import serialize_server_data, deserialize_server_data

# file_transfer.py
class ServerFileTransfer:
    def __init__(self, chunk_size: int = 8192):
        self.chunk_size = chunk_size

    def receive_from_client(self, client_socket: Any) -> Any:
        """Receive data from client using chunked protocol"""
        try:
            # Get length header
            length_header = client_socket.recv(10).decode('utf-8').strip()
            length_info = client_socket.recv(int(length_header)).decode('utf-8')
            total_length = json.loads(length_info)["length"]
            
            # Receive data chunks
            received_data = b""
            while len(received_data) < total_length:
                chunk = client_socket.recv(min(self.chunk_size, total_length - len(received_data)))
                if not chunk:
                    raise Exception("Client connection closed prematurely")
                received_data += chunk
                # Send acknowledgment for the received chunk
                client_socket.send(b'ok')
                print(f"Acknowledged receipt of chunk: {len(received_data)}/{total_length} bytes")

            return deserialize_server_data(received_data)
        except Exception as e:
            raise Exception(f"Server receive error: {str(e)}")


    def send_to_client(self, client_socket: Any, data: Any) -> None:
        """Send data to client using chunked protocol"""
        try:
            serialized_data = serialize_server_data(data)
            total_length = len(serialized_data)
            
            # Send length header
            length_info = serialize_server_data({"length": total_length})
            client_socket.send(f"{len(length_info):<10}".encode('utf-8'))
            client_socket.send(length_info)
            
            # Send data chunks
            for i in range(0, total_length, self.chunk_size):
                chunk = serialized_data[i:i + self.chunk_size]
                client_socket.send(chunk)
                ack = client_socket.recv(2)
                if ack != b'ok':
                    raise Exception("Client acknowledgment error")
        except Exception as e:
            raise Exception(f"Server send error: {str(e)}")