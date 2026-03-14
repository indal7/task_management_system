import re

def is_valid_email(email):
    """Validate email format."""
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(email_regex, email))

def is_valid_password(password):
    """Ensure password meets security requirements."""
    return len(password) >= 8

def validate_task_data(data):
    """Ensure required fields are present in task creation."""
    required_fields = ['title', 'description', 'priority']
    for field in required_fields:
        if field not in data:
            return {'error': f'{field} is required'}
    return None
