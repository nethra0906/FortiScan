from flask import jsonify, abort, g
from sqlalchemy.exc import SQLAlchemyError
from marshmallow import ValidationError
import logging

# Assuming you have these defined in your project
from models import User, db
from schemas import UserSchema  # Only exposes safe fields

logger = logging.getLogger(__name__)

def get_user_by_id(user_id):
    """
    Fetch a user record by user ID with proper validation, authorization,
    and security practices.
    
    Args:
        user_id: The ID of the user to fetch (int or string convertible to int)
    
    Returns:
        JSON response with user data or error message
    """
    # Step 1: Validate user_id is a positive integer
    try:
        user_id = int(user_id)
        if user_id <= 0:
            return jsonify({"error": "User ID must be a positive integer"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid user ID format. Must be a positive integer"}), 400

    # Step 2: Authorization check
    current_user = g.get('current_user')  # Typically set by @login_required or JWT middleware
    
    if not current_user:
        return jsonify({"error": "Authentication required"}), 401
    
    # Allow access if: user is requesting their own record OR user is admin
    is_admin = getattr(current_user, 'is_admin', False) or getattr(current_user, 'role', None) == 'admin'
    
    if not is_admin and current_user.id != user_id:
        return jsonify({"error": "You do not have permission to access this user record"}), 403

    try:
        # Step 3: Use ORM query (never raw SQL with string formatting)
        user = db.session.query(User).filter(User.id == user_id).first()
        
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Step 4: Serialize only safe fields (never include password_hash, etc.)
        user_schema = UserSchema(only=['id', 'username', 'email', 'full_name', 
                                      'created_at', 'is_active', 'role'])
        
        result = user_schema.dump(user)
        
        return jsonify({
            "success": True,
            "data": result
        }), 200

    except SQLAlchemyError as e:
        # Never expose raw DB errors or stack traces
        logger.error(f"Database error when fetching user {user_id}: {str(e)}", exc_info=False)
        return jsonify({"error": "An internal error occurred while fetching user data"}), 500
        
    except Exception as e:
        logger.error(f"Unexpected error fetching user {user_id}: {str(e)}", exc_info=False)
        return jsonify({"error": "An unexpected error occurred"}), 500