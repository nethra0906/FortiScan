from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta, timezone
import secrets
import hashlib
import hmac
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Assuming you have these in your models (SQLAlchemy example)
from your_app.models import db, User, PasswordResetToken

# Create a Blueprint for auth routes
auth_bp = Blueprint('auth', __name__)


def send_password_reset_email(email: str, reset_token: str):
    """Send password reset email with the token (raw token)."""
    # In production, use a proper email service like SendGrid, Mailgun, etc.
    # This is a minimal example using smtplib.
    sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')
    smtp_server = current_app.config.get('MAIL_SERVER')
    smtp_port = current_app.config.get('MAIL_PORT', 587)
    smtp_username = current_app.config.get('MAIL_USERNAME')
    smtp_password = current_app.config.get('MAIL_PASSWORD')

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = "Password Reset Request"

    reset_link = f"{current_app.config.get('FRONTEND_URL', 'http://localhost:3000')}/reset-password?token={reset_token}"

    body = f"""
    You requested a password reset.
    
    Click the link below to reset your password:
    {reset_link}
    
    This link will expire in 60 minutes.
    
    If you did not request this, please ignore this email.
    """
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        current_app.logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        current_app.logger.error(f"Failed to send password reset email to {email}: {e}")


@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset.
    Always return the same response to prevent user enumeration.
    """
    data = request.get_json(silent=True) or {}
    email = data.get('email')

    if not email or not isinstance(email, str):
        return jsonify({"message": "If an account with that email exists, a reset link has been sent."}), 200

    # Find user (but don't reveal existence)
    user = User.query.filter_by(email=email.lower().strip()).first()

    # Always proceed with token generation even if user doesn't exist
    # This prevents timing attacks / enumeration

    # Generate cryptographically secure token (raw token - never store this)
    raw_token = secrets.token_urlsafe(32)

    # Create a secure hash of the token for storage (using SHA-256)
    token_hash = hashlib.sha256(raw_token.encode('utf-8')).digest()

    # Set expiry to 1 hour max
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    # If user exists, create/update reset token record
    if user:
        # Invalidate any existing tokens for this user
        PasswordResetToken.query.filter_by(user_id=user.id).delete()

        reset_entry = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        db.session.add(reset_entry)
        db.session.commit()

        # Send email with the RAW token (user will click the link)
        send_password_reset_email(email, raw_token)

    # Always return the same success message
    return jsonify({
        "message": "If an account with that email exists, a reset link has been sent."
    }), 200


@auth_bp.route('/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using token.
    """
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password or not isinstance(token, str) or not isinstance(new_password, str):
        return jsonify({"error": "Token and new password are required"}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters long"}), 400

    # Find valid token record
    now = datetime.now(timezone.utc)
    reset_entry = PasswordResetToken.query.filter(
        PasswordResetToken.expires_at > now
    ).first()  # Note: In production, better to index and filter by hash if possible

    if not reset_entry:
        return jsonify({"error": "Invalid or expired token"}), 400

    # Constant-time comparison of token hash
    provided_hash = hashlib.sha256(token.encode('utf-8')).digest()
    if not hmac.compare_digest(provided_hash, reset_entry.token_hash):
        return jsonify({"error": "Invalid or expired token"}), 400

    # Token is valid - get the user
    user = User.query.get(reset_entry.user_id)
    if not user:
        # Should not happen if foreign key is set
        db.session.delete(reset_entry)
        db.session.commit()
        return jsonify({"error": "Invalid or expired token"}), 400

    # Hash new password with bcrypt (work factor recommended: 12-14)
    salt = bcrypt.gensalt(rounds=12)
    hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), salt)

    # Update password
    user.password_hash = hashed_password
    # Optionally: user.password_changed_at = datetime.now(timezone.utc)

    # Invalidate token immediately
    db.session.delete(reset_entry)
    db.session.commit()

    current_app.logger.info(f"Password successfully reset for user {user.id}")

    return jsonify({
        "message": "Password has been successfully reset. You can now log in with your new password."
    }), 200