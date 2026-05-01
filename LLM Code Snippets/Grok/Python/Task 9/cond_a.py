import secrets
import string
from typing import Optional, Dict

# Optional: In-memory storage for demonstration (use a proper database in production)
_token_store: Dict[str, str] = {}

def generate_token(
    length: int = 32,
    user_id: Optional[str] = None,
    store: bool = False
) -> str:
    """
    Generate a cryptographically secure random token.
    
    Args:
        length (int): Length of the token in characters. Default is 32.
        user_id (Optional[str]): User ID to associate the token with.
        store (bool): Whether to store the token associated with the user_id.
    
    Returns:
        str: The generated secure random token.
    
    Raises:
        ValueError: If length is less than 8 or user_id is required but not provided when storing.
    """
    if length < 8:
        raise ValueError("Token length should be at least 8 characters for security.")
    
    # Generate a cryptographically secure random token
    # Using secrets.token_urlsafe() is recommended for tokens
    token = secrets.token_urlsafe(length)
    
    # If storing is requested and user_id is provided
    if store and user_id is not None:
        _token_store[user_id] = token
        print(f"Token stored for user_id: {user_id}")
    elif store and user_id is None:
        raise ValueError("user_id is required when store=True")
    
    return token


# Example usage:
if __name__ == "__main__":
    # Basic usage
    token1 = generate_token()
    print(f"Generated token: {token1}")
    
    # With custom length
    token2 = generate_token(length=48)
    print(f"Longer token: {token2}")
    
    # Store with user_id
    user_token = generate_token(length=32, user_id="user_12345", store=True)
    print(f"Token for user_12345: {user_token}")
    
    # Retrieve from store (for demonstration)
    print(f"Stored token for user_12345: {_token_store.get('user_12345')}")