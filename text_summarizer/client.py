import socket
import json
import os
import re
import fitz
from docx import Document

# Define the host and port for the connection
HOST = '127.0.0.1'
PORT = 65432

CHUNK_SIZE = 8192  # 8KB chunks for transfer

def clean_text(text):
    """
    Clean the text to remove problematic characters and normalize whitespace
    """
    # Remove non-printable characters except normal whitespace
    text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove any null bytes
    text = text.replace('\x00', '')
    
    # Strip excessive whitespace
    text = text.strip()
    
    return text

def extract_text_from_pdf(file_path):
    """
    Extract text from PDF while handling images properly
    """
    text_content = []
    try:
        with fitz.open(file_path) as doc:
            for page in doc:
                # Extract text content
                text = page.get_text("text")  # Specify "text" format to avoid other elements
                if text.strip():  # Only add non-empty text
                    text_content.append(clean_text(text))
                
                # Optionally log if page contains images
                image_list = page.get_images()
                if image_list:
                    print(f"Note: Page {page.number + 1} contains {len(image_list)} image(s)")
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")
    
    return "\n".join(text_content)

def read_file(file_path):
    """
    Read the content of the file based on its type.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError("The specified file does not exist.")

    file_extension = file_path.split('.')[-1].lower()
    
    if file_extension == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_extension == "docx":
        try:
            doc = Document(file_path)
            text = "\n".join([clean_text(para.text) for para in doc.paragraphs])
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX file: {str(e)}")
    else:
        raise ValueError("Unsupported file type. Please use a PDF or DOCX file.")

def send_data(sock, data):
    """
    Send data in chunks with a protocol
    """
    try:
        serialized_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
    except UnicodeEncodeError:
        # If UTF-8 encoding fails, try with ASCII and ignore problematic characters
        print("Warning: Some special characters were removed from the text")
        serialized_data = json.dumps(data, ensure_ascii=True).encode('ascii')
    
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

def send_request(operation, file_path):
    client = None
    try:
        # Create a socket and connect to the server
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST, PORT))
        
        print("Reading file...")
        # Read and clean the content of the file
        text = read_file(file_path)
        print(f"Successfully extracted text ({len(text)} characters)")
        
        # Prepare the request data
        request = {
            "operation": operation,
            "text": text
        }
        
        print("Sending data to server...")
        # Send the request using chunked protocol
        send_data(client, request)
        
        print("Waiting for response...")
        # Receive the response using chunked protocol
        response = receive_data(client)
        
        if response.get("status") == "success":
            print(f"\nResult: {response['result']}")
        else:
            print(f"\nError: {response.get('message', 'Unknown error')}")
    
    except FileNotFoundError as e:
        print(f"File error: {str(e)}")
    except json.JSONDecodeError as e:
        print(f"JSON error: {str(e)}")
    except socket.error as e:
        print(f"Socket error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    try:
        file_path = input("Enter the file path (PDF/DOCX): ")
        send_request("summarize", file_path)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")