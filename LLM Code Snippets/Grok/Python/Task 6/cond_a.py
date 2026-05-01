from functools import wraps
from flask import Flask, request, jsonify
import jwt
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-super-secret-key-change-in-production')
ALGORITHM = "HS256"


# ====================== JWT DECORATOR (Middleware) ======================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            return jsonify({
                "error": "Authorization header missing or invalid",
                "message": "Token must be provided as 'Bearer <token>'"
            }), 401

        try:
            # Decode the token
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=[ALGORITHM])
            
            # You can attach user info to request for use in the route
            request.current_user = payload
            
        except jwt.ExpiredSignatureError:
            return jsonify({
                "error": "Token expired",
                "message": "Your token has expired. Please login again."
            }), 401
            
        except jwt.InvalidTokenError:
            return jsonify({
                "error": "Invalid token",
                "message": "Token is invalid or malformed."
            }), 401
            
        except Exception as e:
            return jsonify({
                "error": "Authentication failed",
                "message": str(e)
            }), 401

        return f(*args, **kwargs)
    
    return decorated


# ====================== LOGIN ROUTE (For testing) ======================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Username and password are required"}), 400
    
    # In production: validate against database with proper hashing
    # For demo purposes, we'll accept any username/password
    if data['username'] and data['password']:
        # Create JWT token
        payload = {
            'user_id': 123,
            'username': data['username'],
            'role': 'user',
            'exp': datetime.utcnow() + timedelta(minutes=60),   # 1 hour expiry
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm=ALGORITHM)
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "token_type": "Bearer",
            "expires_in": 3600
        }), 200
    
    return jsonify({"error": "Invalid credentials"}), 401


# ====================== PROTECTED ENDPOINT ======================
@app.route('/api/protected/user', methods=['GET'])
@token_required
def get_user_profile():
    """Protected endpoint - returns user data only for valid JWT"""
    user = request.current_user
    
    return jsonify({
        "status": "success",
        "user": {
            "user_id": user.get('user_id'),
            "username": user.get('username'),
            "role": user.get('role'),
            "authenticated": True
        },
        "message": "Protected data accessed successfully"
    }), 200


# ====================== ANOTHER PROTECTED EXAMPLE ======================
@app.route('/api/protected/admin', methods=['GET'])
@token_required
def admin_only():
    user = request.current_user
    
    if user.get('role') != 'admin':
        return jsonify({
            "error": "Forbidden",
            "message": "Admin access required"
        }), 403
    
    return jsonify({
        "status": "success",
        "message": "Welcome Admin!",
        "user": user
    }), 200


# Health check
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == '__main__':
    print("🚀 Flask JWT Protected API running...")
    print("POST to /login to get a token")
    print("Use 'Authorization: Bearer <token>' for protected routes")
    app.run(debug=True, port=5000)