# server.py
import threading
from connection import ServerConnection
from file_transfer import ServerFileTransfer
from utils import create_server_response
from gemini_handler import GeminiHandler

class DocumentServer:
    def __init__(self, host='127.0.0.1', port=65432):
        self.connection = ServerConnection(host, port)
        self.transfer = ServerFileTransfer()
        try:
            # Hardcoded Gemini API Key
            GEMINI_API_KEY = 'AIzaSyAOQ9GIThEhIz68y6xEfDHdWmuNNiYSdCQ'
            self.gemini_handler = GeminiHandler(api_key=GEMINI_API_KEY)
        except Exception as e:
            print(f"Failed to initialize Gemini handler: {e}")
            raise

    def handle_client(self, client_socket, address):
        print(f"Handling client from {address}")
        try:
            # Receive request
            request = self.transfer.receive_from_client(client_socket)
            print(f"Received request: {request}")
            
            # Process request
            operation = request.get('operation')
            text = request.get('data')
            
            if operation == "summarize":
                if not text:
                    response = create_server_response("error", message="No text provided")
                else:
                    result = self.gemini_handler.summarize_text(text)
                    response = create_server_response("success", data=result)
            else:
                response = create_server_response("error", message=f"Invalid operation: {operation}")
            
            # Send response
            self.transfer.send_to_client(client_socket, response)
            print(f"Response sent to client {address}")
            
        except Exception as e:
            print(f"Error handling client {address}: {e}")
            try:
                self.transfer.send_to_client(
                    client_socket, 
                    create_server_response("error", message=str(e))
                )
            except Exception as send_error:
                print(f"Failed to send error response to client {address}: {send_error}")
        finally:
            try:
                client_socket.close()
                print(f"Closed connection to client {address}")
            except Exception as e:
                print(f"Error closing client socket {address}: {e}")

    def start(self):
        try:
            server_socket = self.connection.create_socket()
            print(f"Server started successfully on {self.connection.host}:{self.connection.port}")
            
            while True:
                client_socket, address = self.connection.accept_client()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True  # Make thread daemon so it exits when main thread exits
                client_thread.start()
                print(f"Started handling thread for client {address}")
                
        except KeyboardInterrupt:
            print("\nReceived shutdown signal. Shutting down server...")
        except Exception as e:
            print(f"Critical server error: {e}")
        finally:
            self.connection.close()

if __name__ == "__main__":
    try:
        server = DocumentServer()
        print("Starting document server...")
        server.start()
    except Exception as e:
        print(f"Failed to start server: {e}")
