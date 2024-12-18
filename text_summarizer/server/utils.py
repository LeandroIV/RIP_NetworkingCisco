# utils.py
import traceback
import json
from typing import Any, Dict

def format_error(error: Exception) -> str:
    """Format server-side error message with traceback"""
    return f"Server Error: {str(error)}\n{traceback.format_exc()}"

def create_server_response(status: str, data: Any = None, message: str = None) -> Dict[str, Any]:
    """Create standardized server response"""
    response = {"status": status}
    if data is not None:
        response["data"] = data
    if message is not None:
        response["message"] = message
    return response

def serialize_server_data(data: Any) -> bytes:
    """Serialize data for server transmission"""
    return json.dumps(data, ensure_ascii=False).encode('utf-8')

def deserialize_server_data(data: bytes) -> Any:
    """Deserialize received client data"""
    return json.loads(data.decode('utf-8'))