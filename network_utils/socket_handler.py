import socket
import json
from typing import Dict, Any
from security.ssl_handler import SSLConnectionHandler


class RIPSocketHandler:
    def __init__(self, router_id: str, host: str = 'localhost', port: int = 0):
        self.router_id = router_id
        self.host = host
        self.port = port
        self.socket, self.ssl_context = SSLConnectionHandler.create_secure_socket(
            host, port, is_server=True
        )

    def send_rip_update(self, dest_socket: socket.socket, routing_table: Dict):
        packet = {
            "router_id": self.router_id,
            "routing_table": routing_table
        }
        serialized_packet = json.dumps(packet).encode('utf-8')

        # Wrap socket with SSL
        secure_socket = SSLConnectionHandler.wrap_socket(
            dest_socket, self.ssl_context, server_side=False
        )
        secure_socket.send(serialized_packet)

    def receive_rip_update(self) -> Dict[str, Any]:
        client_socket, _ = self.socket.accept()
        secure_socket = SSLConnectionHandler.wrap_socket(
            client_socket, self.ssl_context, server_side=True
        )

        data = secure_socket.recv(4096)
        return json.loads(data.decode('utf-8'))