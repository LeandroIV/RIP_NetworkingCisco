import socket
import json

# Define the server's host and port (must match the server)
HOST = '127.0.0.1'
PORT = 65432

def send_request(text):
    try:
        # Create a socket and connect to the server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        
        # Prepare the request data in JSON format
        request = {
            "text": text
        }
        client.send(json.dumps(request).encode('utf-8'))
        
        # Receive the server's response
        response_data = client.recv(1024).decode('utf-8')
        response = json.loads(response_data)
        
        if response.get("status") == "success":
            print(f"\nResult: {response['result']}\n")
        else:
            print(f"Error: {response.get('message')}")

    except Exception as e:
        print(f"Connection error: {str(e)}")
    
    finally:
        client.close()

if __name__ == "__main__":
    # Example usage:
    text = input("Enter the text to summarize: ")
    send_request(text)
