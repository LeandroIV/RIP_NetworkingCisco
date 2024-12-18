import socket
import os
import json

class RIPSocketHandler:
    def __init__(self, router_id, host='127.0.0.1', port=65432, save_directory='server_files'):
        """Initialize the socket handler for a router."""
        self.router_id = router_id
        self.host = host
        self.port = port
        self.save_directory = save_directory
        os.makedirs(save_directory, exist_ok=True)  # Ensure the save directory exists

    def start_server(self):
        """Start the server to handle RIP updates and file transfers."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"Router {self.router_id} listening on {self.host}:{self.port}")

            while True:
                conn, addr = server_socket.accept()
                with conn:
                    print(f"Router {self.router_id} connected by {addr}")

                    # Receive the message type (RIP update or file transfer)
                    message_type = conn.recv(1024).decode()

                    if message_type == "RIP_UPDATE":
                        self._receive_rip_update(conn)
                    elif message_type == "FILE_TRANSFER":
                        self._receive_file(conn)
                    else:
                        print("Unknown message type received.")

    def _receive_rip_update(self, conn):
        """Receive and process a RIP update."""
        data = conn.recv(4096).decode()
        rip_packet = json.loads(data)

        print(f"Received RIP update from Router {rip_packet['router_id']}:")
        print(json.dumps(rip_packet['routing_table'], indent=2))

    def _receive_file(self, conn):
        """Receive a file and save it to the designated directory."""
        # Receive file metadata
        file_name = conn.recv(1024).decode()
        if not file_name:
            print("No file name received. Closing connection.")
            return

        file_size = int(conn.recv(1024).decode())
        print(f"Receiving file: {file_name} ({file_size} bytes)")

        # Receive file data
        file_path = os.path.join(self.save_directory, file_name)
        with open(file_path, 'wb') as file:
            received_size = 0
            while received_size < file_size:
                data = conn.recv(1024)
                if not data:
                    break
                file.write(data)
                received_size += len(data)

        print(f"File {file_name} received successfully.")

    def send_file(self, file_path, target_host, target_port):
        """Send a file to another router."""
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((target_host, target_port))
            print(f"Router {self.router_id} connected to {target_host}:{target_port}")

            # Send message type
            client_socket.sendall(b"FILE_TRANSFER")

            # Send file metadata
            client_socket.sendall(file_name.encode())
            client_socket.sendall(str(file_size).encode())

            # Send file data
            with open(file_path, 'rb') as file:
                while chunk := file.read(1024):
                    client_socket.sendall(chunk)

            print(f"File {file_name} sent successfully.")

    def send_rip_update(self, target_host, target_port, routing_table):
        """Send a RIP update to another router."""
        rip_packet = {
            "router_id": self.router_id,
            "routing_table": routing_table
        }
        serialized_packet = json.dumps(rip_packet).encode('utf-8')

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((target_host, target_port))
            print(f"Router {self.router_id} connected to {target_host}:{target_port}")

            # Send message type
            client_socket.sendall(b"RIP_UPDATE")

            # Send RIP packet
            client_socket.sendall(serialized_packet)

            print(f"RIP update sent successfully to {target_host}:{target_port}.")

# Example Usage
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="RIP Socket Handler for File Transfer and Updates")
    parser.add_argument("role", choices=["server", "client"], help="Role: server or client")
    parser.add_argument("--router_id", default="R1", help="Router ID")
    parser.add_argument("--host", default="127.0.0.1", help="Host address")
    parser.add_argument("--port", type=int, default=65432, help="Port number")
    parser.add_argument("--file", help="Path to the file (client only)")
    parser.add_argument("--routing_table", type=json.loads, help="Routing table (client only, as JSON)")
    parser.add_argument("--save_dir", default="server_files", help="Directory to save received files (server only)")

    args = parser.parse_args()

    handler = RIPSocketHandler(router_id=args.router_id, host=args.host, port=args.port, save_directory=args.save_dir)

    if args.role == "server":
        handler.start_server()
    elif args.role == "client":
        if args.file:
            handler.send_file(args.file, args.host, args.port)
        elif args.routing_table:
            handler.send_rip_update(args.host, args.port, args.routing_table)
        else:
            print("Error: Provide either --file or --routing_table for client role.")