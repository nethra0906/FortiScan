import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional

def generate_secure_session_token(
    expiry_minutes: int = 60,
    token_bytes: int = 32
) -> Tuple[str, str, datetime]:
    """
    Generates a cryptographically secure random token for use as a session identifier or API key.
    
    Requirements satisfied:
    - Uses ONLY secrets.token_urlsafe() for token generation
    - Provides at least 256 bits (32 bytes) of entropy
    - Returns the raw token to the caller (to be transmitted once)
    - Computes and returns a SHA-256 hash for secure storage
    - Sets an explicit expiry timestamp
    - Never logs or prints the raw token
    
    Args:
        expiry_minutes: How long the token should be valid (default: 60 minutes)
        token_bytes: Number of random bytes (default: 32 → 256 bits entropy)
    
    Returns:
        Tuple containing:
        - raw_token: The cryptographically secure token (transmit this once)
        - token_hash: SHA-256 hex digest to store in the database
        - expiry: Explicit expiry datetime (timezone-aware UTC)
    """
    # (1) Generate token using secrets module exclusively (never random, uuid4 alone, or raw urandom)
    # token_urlsafe(32) gives ~43 characters of base64url with 32 bytes (256 bits) entropy
    raw_token: str = secrets.token_urlsafe(token_bytes)
    
    # (2) Compute SHA-256 hash for storage (never store raw token)
    token_hash: str = hashlib.sha256(raw_token.encode('utf-8')).hexdigest()
    
    # (3) Set explicit expiry timestamp (timezone-aware UTC)
    expiry: datetime = datetime.now(timezone.utc) + timedelta(minutes=expiry_minutes)
    
    # IMPORTANT: Do NOT log, print, or expose raw_token anywhere in this function
    # The caller is responsible for transmitting it securely once and then discarding it.
    
    return raw_token, token_hash, expiry


# Example usage (for illustration only — do not include in production code)
if __name__ == "__main__":
    # This block demonstrates correct usage; in real code, never print raw_token in logs
    token, token_hash, expiry = generate_secure_session_token(expiry_minutes=30)
    
    print("Token generated successfully.")
    print(f"Store in DB → hash: {token_hash}")
    print(f"Expires at: {expiry.isoformat()}")
    # Never do: print("Raw token:", token)  ← SECURITY VIOLATION