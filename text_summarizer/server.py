import socket
import threading
import json
from gemini_handler import GeminiHandler

# Define the server's host and port
HOST = '127.0.0.1'
PORT = 65432

CHUNK_SIZE = 8192  # 8KB chunks for transfer

# Initialize Gemini handler with the API key
gemini_handler = GeminiHandler(api_key='AIzaSyAOQ9GIThEhIz68y6xEfDHdWmuNNiYSdCQ')

def receive_data(sock):
    """
    Receive data in chunks
    """
    # Get the length header size
    length_header = sock.recv(10).decode('utf-8').strip()
    length_info = sock.recv(int(length_header)).decode('utf-8')
    total_length = json.loads(length_info)["length"]
    
    received_data = b""
    while len(received_data) < total_length:
        chunk = sock.recv(min(CHUNK_SIZE, total_length - len(received_data)))
        if not chunk:
            raise Exception("Connection closed before receiving all data")
        received_data += chunk
        sock.send(b'ok')
    
    return json.loads(received_data.decode('utf-8'))

def send_data(sock, data):
    """
    Send data in chunks
    """
    serialized_data = json.dumps(data).encode('utf-8')
    total_length = len(serialized_data)
    
    # Send total length first
    length_info = json.dumps({"length": total_length}).encode('utf-8')
    sock.send(f"{len(length_info):<10}".encode('utf-8'))
    sock.send(length_info)
    
    # Send data in chunks
    for i in range(0, total_length, CHUNK_SIZE):
        chunk = serialized_data[i:i + CHUNK_SIZE]
        sock.send(chunk)
        # Wait for acknowledgment
        ack = sock.recv(2)
        if ack != b'ok':
            raise Exception("Data transfer error")

def handle_client_connection(client_socket):
    try:
        # Receive the request using chunked protocol
        request = receive_data(client_socket)
        
        operation = request.get('operation')
        text = request.get('text')

        if operation == "summarize":
            result = gemini_handler.summarize_text(text)
        else:
            result = "Invalid operation specified."
        
        # Send the response using chunked protocol
        response = {
            "status": "success",
            "result": result
        }
        send_data(client_socket, response)
    
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e)
        }
        try:
            send_data(client_socket, error_response)
        except:
            pass  # If we can't send the error, there's not much we can do
    
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    try:
        while True:
            client_socket, client_address = server.accept()
            print(f"Connection from {client_address}")
            client_handler = threading.Thread(
                target=handle_client_connection, 
                args=(client_socket,)
            )
            client_handler.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()