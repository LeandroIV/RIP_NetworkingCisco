# client/utils.py
import re
import json
from typing import Any

def format_error(error: Exception) -> str:
    """Format client-side error message"""
    return f"Client Error: {str(error)}"

def clean_text(text: str) -> str:
    """Clean and normalize text for transmission"""
    text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\x00', '')
    return text.strip()

def create_client_request(operation: str, data: Any) -> dict:
    """Create standardized client request"""
    return {
        "operation": operation,
        "data": data
    }

def serialize_client_data(data: Any) -> bytes:
    """Serialize data for client transmission"""
    return json.dumps(data, ensure_ascii=False).encode('utf-8')

def deserialize_client_data(data: bytes) -> Any:
    """Deserialize received server data"""
    return json.loads(data.decode('utf-8'))