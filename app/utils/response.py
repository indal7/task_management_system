# app/utils/response.py
from flask import jsonify
from datetime import datetime
from typing import Any, Dict, Optional

class Response:
    """Single standardized API response utility."""
    
    @staticmethod
    def send(
        success: bool = True,
        message: str = "",
        data: Any = None,
        status_code: int = 200,
        **kwargs
    ):
        """
        Single method to create all API responses.
        
        Args:
            success (bool): Whether the operation was successful
            message (str): Response message
            data (Any): Response data (can be dict, list, string, etc.)
            status_code (int): HTTP status code
            **kwargs: Any additional fields to include in response
        
        Returns:
            Flask response tuple (json, status_code)
        """
        response_data = {
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add any additional fields passed via kwargs
        response_data.update(kwargs)
        
        return jsonify(response_data), status_code

# Convenience methods for common responses
def success_response(message="Success", data=None, status_code=200, **kwargs):
    """Quick success response."""
    return Response.send(True, message, data, status_code, **kwargs)

def error_response(message="Error occurred", data=None, status_code=400, **kwargs):
    """Quick error response."""
    return Response.send(False, message, data, status_code, **kwargs)

def created_response(message="Created successfully", data=None, **kwargs):
    """Quick created response."""
    return Response.send(True, message, data, 201, **kwargs)

def not_found_response(message="Resource not found", data=None, **kwargs):
    """Quick not found response."""
    return Response.send(False, message, data, 404, **kwargs)

def validation_error_response(message="Validation failed", data=None, **kwargs):
    """Quick validation error response."""
    return Response.send(False, message, data, 422, **kwargs)

def server_error_response(message="Internal server error", data=None, **kwargs):
    """Quick server error response."""
    return Response.send(False, message, data, 500, **kwargs)

def unauthorized_response(message="Unauthorized", data=None, **kwargs):
    """Quick unauthorized response."""
    return Response.send(False, message, data, 401, **kwargs)

def forbidden_response(message="Forbidden", data=None, **kwargs):
    """Quick forbidden response."""
    return Response.send(False, message, data, 403, **kwargs)