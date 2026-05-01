from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import check_password_hash
import logging

# Assuming you have a User model and database setup
# from your_app.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint with session management.
    
    Expects JSON body:
    {
        "username": "john_doe",
        "password": "secret123"
    }
    
    Returns:
        JSON response with success/failure status
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Input validation
        if not username or not password:
            return jsonify({
                "success": False, 
                "message": "Username and password are required"
            }), 400
        
        # Fetch user from database
        user = User.query.filter_by(username=username).first()
        
        if not user:
            # Use generic message for security (don't reveal if username exists)
            return jsonify({
                "success": False, 
                "message": "Invalid username or password"
            }), 401
        
        # Verify password
        if not check_password_hash(user.password_hash, password):
            return jsonify({
                "success": False, 
                "message": "Invalid username or password"
            }), 401
        
        # Clear any existing session (optional but good practice)
        session.clear()
        
        # Create new session
        session['user_id'] = user.id
        session['username'] = user.username
        session.permanent = True  # Makes session last for PERMANENT_SESSION_LIFETIME
        
        # Optional: Store additional user info in session
        # session['role'] = user.role
        # session['email'] = user.email
        
        logging.info(f"User {username} logged in successfully")
        
        return jsonify({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                # Add other non-sensitive fields as needed
                # "email": user.email,
                # "role": user.role
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "An error occurred during login"
        }), 500