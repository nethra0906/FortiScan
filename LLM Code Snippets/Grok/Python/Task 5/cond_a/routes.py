from flask import Blueprint, request, jsonify, render_template
from . import auth  # or from your auth module

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
    
    from models import User
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Always send email (even if user doesn't exist) to prevent email enumeration
        auth.send_password_reset_email(user)
    
    # Always return success to avoid revealing user existence
    return jsonify({
        "message": "If an account with that email exists, a password reset link has been sent."
    }), 200


@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data.get('new_password')
    
    if not new_password or len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400
    
    success, message = auth.reset_password(token, new_password)
    
    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 400