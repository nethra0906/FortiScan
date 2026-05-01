from flask import Blueprint, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from typing import Optional, Dict, Any

# Initialize extensions (usually done in your app factory or main app)
db = SQLAlchemy()

# Define the User model (example)
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Blueprint or route function
def get_user_by_id(user_id: int) -> tuple:
    """
    Fetch a user record by user ID.
    
    Args:
        user_id (int): The ID of the user to fetch
        
    Returns:
        tuple: (JSON response, HTTP status code)
    """
    try:
        user = User.query.get(user_id)
        
        if user is None:
            return jsonify({
                "error": "User not found",
                "message": f"No user found with ID {user_id}"
            }), 404
            
        return jsonify({
            "success": True,
            "data": user.to_dict()
        }), 200
        
    except Exception as e:
        # Log the error in production
        return jsonify({
            "error": "Internal server error",
            "message": "Failed to fetch user"
        }), 500


# Alternative: As a Flask route (most common pattern)
def create_user_routes():
    user_bp = Blueprint('users', __name__)
    
    @user_bp.route('/users/<int:user_id>', methods=['GET'])
    def get_user(user_id: int):
        """GET /users/<user_id>"""
        return get_user_by_id(user_id)
    
    return user_bp