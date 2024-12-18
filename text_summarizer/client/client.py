import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, 
                           QVBoxLayout, QWidget, QFileDialog, QProgressBar,
                           QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

from docx import Document
import fitz

from connection import ClientConnection
from file_transfer import ClientFileTransfer
from utils import clean_text, create_client_request

class ProcessingThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.connection = ClientConnection()
        self.transfer = ClientFileTransfer()

    def extract_text_from_pdf(self, file_path):
        """Extract text content from PDF file"""
        text_content = []
        try:
            with fitz.open(file_path) as doc:
                total_pages = len(doc)
                for page_num, page in enumerate(doc, 1):
                    self.progress.emit(f"Processing page {page_num}/{total_pages}")
                    text = page.get_text("text")
                    if text.strip():
                        text_content.append(clean_text(text))
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        return "\n".join(text_content)

    def read_file(self):
        """Read and extract text from supported file types"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError("The specified file does not exist.")

        file_extension = os.path.splitext(self.file_path)[1].lower()
        
        if file_extension == ".pdf":
            return self.extract_text_from_pdf(self.file_path)
        elif file_extension == ".docx":
            try:
                doc = Document(self.file_path)
                text = "\n".join([clean_text(para.text) for para in doc.paragraphs])
                return text
            except Exception as e:
                raise Exception(f"Error reading DOCX file: {str(e)}")
        else:
            raise ValueError("Unsupported file type. Please use a PDF or DOCX file.")

    def run(self):
        try:
            # Read file
            self.progress.emit("Reading file...")
            text = self.read_file()
            
            # Create and connect socket
            self.progress.emit("Connecting to server...")
            self.connection.create_socket()
            self.connection.connect_to_server()
            
            # Prepare and send request
            request = create_client_request("summarize", text)
            self.progress.emit("Sending request to server...")
            self.transfer.send_to_server(self.connection._socket, request)
            
            # Receive response
            self.progress.emit("Waiting for server response...")
            response = self.transfer.receive_from_server(self.connection._socket)
            
            self.finished.emit(response)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.connection.close()

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
            
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(('.pdf', '.docx')):
                    main_window = self.window()
                    if main_window:
                        main_window.handle_file_selection(file_path)
                    break

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Document Processor")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
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
        self.file_label.setFont(QFont('Arial', 12))
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
                <p>{response.get('data', '')}</p>
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