import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QWidget, QFileDialog, QProgressBar,
                           QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

import socket
import json
import re
import fitz
from docx import Document

class ProcessingThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.HOST = '127.0.0.1'
        self.PORT = 65432
        self.CHUNK_SIZE = 8192

    def clean_text(self, text):
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        text = re.sub(r'\s+', ' ', text)
        text = text.replace('\x00', '')
        return text.strip()

    def extract_text_from_pdf(self, file_path):
        text_content = []
        try:
            with fitz.open(file_path) as doc:
                total_pages = len(doc)
                for page_num, page in enumerate(doc, 1):
                    self.progress.emit(f"Processing page {page_num}/{total_pages}")
                    text = page.get_text("text")
                    if text.strip():
                        text_content.append(self.clean_text(text))
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        return "\n".join(text_content)

    def read_file(self):
        if not os.path.exists(self.file_path):
            raise FileNotFoundError("The specified file does not exist.")

        file_extension = self.file_path.split('.')[-1].lower()
        
        if file_extension == "pdf":
            return self.extract_text_from_pdf(self.file_path)
        elif file_extension == "docx":
            try:
                doc = Document(self.file_path)
                text = "\n".join([self.clean_text(para.text) for para in doc.paragraphs])
                return text
            except Exception as e:
                raise Exception(f"Error reading DOCX file: {str(e)}")
        else:
            raise ValueError("Unsupported file type. Please use a PDF or DOCX file.")

    def send_data(self, sock, data):
        """
        Send data in chunks with proper protocol matching
        """
        serialized_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
        total_length = len(serialized_data)
        
        # Send total length first
        length_info = json.dumps({"length": total_length}).encode('utf-8')
        sock.send(f"{len(length_info):<10}".encode('utf-8'))
        sock.send(length_info)
        
        # Send data in chunks
        for i in range(0, total_length, self.CHUNK_SIZE):
            chunk = serialized_data[i:i + self.CHUNK_SIZE]
            sock.send(chunk)
            # Wait for acknowledgment
            ack = sock.recv(2)
            if ack != b'ok':
                raise Exception("Data transfer error")
            progress = (i + len(chunk)) / total_length * 100
            self.progress.emit(f"Sending data: {progress:.1f}%")

    def receive_data(self, sock):
        """
        Receive data in chunks with proper protocol matching
        """
        # Get the length header size
        length_header = sock.recv(10).decode('utf-8').strip()
        length_info = sock.recv(int(length_header)).decode('utf-8')
        total_length = json.loads(length_info)["length"]
        
        received_data = b""
        while len(received_data) < total_length:
            chunk = sock.recv(min(self.CHUNK_SIZE, total_length - len(received_data)))
            if not chunk:
                raise Exception("Connection closed before receiving all data")
            received_data += chunk
            sock.send(b'ok')  # Send acknowledgment for each chunk
            progress = len(received_data) / total_length * 100
            self.progress.emit(f"Receiving response: {progress:.1f}%")
        
        return json.loads(received_data.decode('utf-8'))

    def run(self):
        client = None
        try:
            # Read file
            self.progress.emit("Reading file...")
            text = self.read_file()
            
            # Connect to server
            self.progress.emit("Connecting to server...")
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.settimeout(30)
            client.connect((self.HOST, self.PORT))
            
            # Prepare request
            request = {
                "operation": "summarize",
                "text": text
            }
            
            # Send request
            self.progress.emit("Sending request to server...")
            self.send_data(client, request)
            
            # Receive response
            self.progress.emit("Waiting for server response...")
            response = self.receive_data(client)
            
            self.finished.emit(response)
            
        except socket.timeout:
            self.error.emit("Connection timed out. Please check if the server is running.")
        except ConnectionRefusedError:
            self.error.emit("Could not connect to server. Please check if the server is running.")
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if client:
                client.close()

class DropArea(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #999;
                border-radius: 5px;
                background-color: #f0f0f0;
                min-height: 100px;
            }
        """)
        
        layout = QVBoxLayout()
        self.label = QLabel("Drag & Drop PDF or DOCX file here\nor click to browse")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            # Check if any of the URLs end with acceptable extensions
            for url in mime_data.urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.pdf', '.docx')):
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        QFrame {
                            border: 2px dashed #4a9eff;
                            border-radius: 5px;
                            background-color: #e6f3ff;
                            min-height: 100px;
                        }
                    """)
                    return

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #999;
                border-radius: 5px;
                background-color: #f0f0f0;
                min-height: 100px;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #999;
                border-radius: 5px;
                background-color: #f0f0f0;
                min-height: 100px;
            }
        """)
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            # Get the first valid file
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.pdf', '.docx')):
                    # Get the MainWindow instance
                    main_window = self.window()
                    if main_window:
                        main_window.handle_file_selection(file_path)
                    break

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Processor")
        self.setMinimumWidth(800)  # Increased width
        self.setMinimumHeight(600)  # Increased height
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Document Processor")
        title.setFont(QFont('Arial', 24, QFont.Bold))  
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Drop Area
        self.drop_area = DropArea()
        self.drop_area.mousePressEvent = self.browse_files
        layout.addWidget(self.drop_area)
        
        # File Info
        self.file_label = QLabel()
        self.file_label.setFont(QFont('Arial', 14))  
        self.file_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.file_label)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        self.progress_bar.setMinimumHeight(30)
        layout.addWidget(self.progress_bar)
        
        # Process Button
        self.process_button = QPushButton("Process Document")
        self.process_button.setFont(QFont('Arial', 14))
        self.process_button.setEnabled(False)
        self.process_button.clicked.connect(self.process_file)
        self.process_button.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QPushButton:hover:!disabled {
                background-color: #3d8be6;
            }
        """)

        layout.addWidget(self.process_button)
        
        # Results Area
        self.results_area = QTextEdit()
        self.results_area.setFont(QFont('Arial', 12))  
        self.results_area.setReadOnly(True)
        self.results_area.setPlaceholderText("Processing results will appear here...")
        self.results_area.setMinimumHeight(300)
        layout.addWidget(self.results_area)

    def browse_files(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Document",
            "",
            "Documents (*.pdf *.docx)"
        )
        if file_path:
            self.handle_file_selection(file_path)

    def handle_file_selection(self, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in ['.pdf', '.docx']:
            self.current_file = file_path
            self.file_label.setText(f"Selected file: {os.path.basename(file_path)}")
            self.process_button.setEnabled(True)
            self.results_area.clear()
        else:
            self.file_label.setText("Error: Please select a PDF or DOCX file")
            self.process_button.setEnabled(False)

    def process_file(self):
        self.process_button.setEnabled(False)
        self.progress_bar.show()
        self.progress_bar.setFormat("Starting process...")
        self.progress_bar.setValue(0)
        
        self.thread = ProcessingThread(self.current_file)
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.handle_result)
        self.thread.error.connect(self.handle_error)
        self.thread.start()

    def update_progress(self, message):
        self.progress_bar.setFormat(message)
        if "%" in message:
            try:
                value = float(message.split(":")[1].strip().rstrip("%"))
                self.progress_bar.setValue(int(value))
            except:
                pass

    def handle_result(self, response):
        self.process_button.setEnabled(True)
        self.progress_bar.hide()
        
        if response.get("status") == "success":
            self.results_area.setHtml(f"""
                <h3 style='color: #4a9eff;'>Processing Complete</h3>
                <p>{response['result']}</p>
            """)
        else:
            self.results_area.setHtml(f"""
                <h3 style='color: #ff4a4a;'>Error</h3>
                <p>{response.get('message', 'Unknown error')}</p>
            """)

    def handle_error(self, error_message):
        self.process_button.setEnabled(True)
        self.progress_bar.hide()
        self.results_area.setHtml(f"""
            <h3 style='color: #ff4a4a;'>Error</h3>
            <p>{error_message}</p>
        """)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())