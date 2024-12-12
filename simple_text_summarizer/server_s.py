import socket
import threading
import json
from gemini_handler_s import GeminiHandler

# Define the server's host and port
HOST = '127.0.0.1'
PORT = 65432  # You can use any available port

# Initialize Gemini handler with the API key
gemini_handler = GeminiHandler(api_key='AIzaSyAOQ9GIThEhIz68y6xEfDHdWmuNNiYSdCQ')

def handle_client_connection(client_socket):
    try:
        # Receive the request from the client
        request_data = client_socket.recv(1024).decode('utf-8')
        
        if not request_data:
            return
        
        # Parse the request data (JSON format)
        request = json.loads(request_data)
        text = request.get('text')
        
        # Summarize the text
        result = gemini_handler.summarize_text(text)
        
        # Send the result back to the client
        response = {
            "status": "success",
            "result": result
        }
        client_socket.send(json.dumps(response).encode('utf-8'))
    
    except Exception as e:
        error_response = {
            "status": "error",
            "message": str(e)
        }
        client_socket.send(json.dumps(error_response).encode('utf-8'))
    
    finally:
        client_socket.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    while True:
        client_socket, client_address = server.accept()
        print(f"Connection from {client_address}")
        client_handler = threading.Thread(target=handle_client_connection, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_server()
