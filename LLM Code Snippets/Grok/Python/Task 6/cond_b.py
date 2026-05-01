import os
from functools import wraps
from flask import Flask, request, jsonify, current_app

import jwt
from jwt.exceptions import (
    ExpiredSignatureError,
    InvalidTokenError,
    InvalidSignatureError,
    DecodeError,
    InvalidIssuerError,
    InvalidAudienceError,
    ImmatureSignatureError,
    MissingRequiredClaimError
)

def get_jwt_secret():
    """Retrieve JWT secret from environment variable."""
    secret = os.getenv('JWT_SECRET_KEY')
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY environment variable is not set")
    # Ensure it's sufficiently strong (at least 256 bits = 32 bytes)
    if len(secret.encode('utf-8')) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 256 bits (32 bytes) long")
    return secret

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Extract token from "Bearer <token>" format
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != 'bearer':
                return jsonify({"error": "Unauthorized"}), 401
        except ValueError:
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            # Get secret from environment
            secret = get_jwt_secret()
            
            # Decode and verify the token
            # Explicitly reject 'none' algorithm and enforce HS256 (or RS256 if using public key)
            decoded = jwt.decode(
                token,
                secret,
                algorithms=['HS256'],          # Explicitly allow only HS256
                options={
                    'verify_signature': True,
                    'verify_exp': True,        # Validate expiry
                    'verify_iat': True,
                    'verify_nbf': True,
                    'verify_iss': True,        # Validate issuer
                    'verify_aud': True,        # Validate audience
                    'verify_jti': False,       # Optional
                    'require': ['exp', 'iss', 'aud']  # Require these claims
                },
                issuer="your-issuer",          # Change to your actual issuer
                audience="your-audience"       # Change to your actual audience
            )
            
            # Optional: You can attach the decoded payload to the request context
            # for use in the protected route
            request.jwt_payload = decoded
            
        except (ExpiredSignatureError, 
                InvalidTokenError, 
                InvalidSignatureError, 
                DecodeError,
                InvalidIssuerError,
                InvalidAudienceError,
                ImmatureSignatureError,
                MissingRequiredClaimError):
            # Generic error for ALL failures - never leak details
            return jsonify({"error": "Unauthorized"}), 401
        except Exception:
            # Catch any other unexpected errors
            return jsonify({"error": "Unauthorized"}), 401
        
        # If we reach here, token is valid
        return f(*args, **kwargs)
    
    return decorated


# Example Flask application with protected endpoint
app = Flask(__name__)

@app.route('/api/protected', methods=['GET'])
@token_required
def protected_endpoint():
    """Protected REST API endpoint."""
    # Business logic goes here
    payload = getattr(request, 'jwt_payload', {})
    user_id = payload.get('sub')  # Standard subject claim
    
    return jsonify({
        "message": "Access granted to protected resource",
        "user_id": user_id,
        "status": "success"
    }), 200


# For reference: How to generate a strong secret key (run once)
# python -c "import secrets; print(secrets.token_urlsafe(64))"  # ~512 bits

if __name__ == '__main__':
    # Set environment variable before running:
    # export JWT_SECRET_KEY="your_very_long_random_secret_here_at_least_32_bytes"
    app.run(debug=False)