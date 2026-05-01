# user_db.py
"""
Database module for User entity using Flask + SQLAlchemy conventions.
Secure, type-safe, and follows best practices.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import QueuePool

# ----------------------------------------------------------------------
# Base and Model
# ----------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(nullable=False)  # Never store plain passwords
    full_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def to_dict(self) -> Dict[str, Any]:
        """Safe serialization - excludes sensitive fields"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


# ----------------------------------------------------------------------
# Database Manager
# ----------------------------------------------------------------------

db = SQLAlchemy(model_class=Base)


def init_db(app):
    """Initialize database with Flask app and secure connection pooling"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'poolclass': QueuePool,
        'pool_size': 10,           # Sensible default for most apps
        'max_overflow': 20,
        'pool_timeout': 30,        # seconds
        'pool_recycle': 3600,      # prevent stale connections
        'pool_pre_ping': True,     # validate connections before use
    }

    db.init_app(app)

    # Create tables (use migrations in production - Alembic recommended)
    with app.app_context():
        db.create_all()


# ----------------------------------------------------------------------
# Input Validation Helpers
# ----------------------------------------------------------------------

def _validate_string(value: Any, field_name: str, max_length: int = 255) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or not value.strip():
        raise ValueError(f"{field_name} cannot be empty")
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long (max {max_length} characters)")
    return value.strip()


def _validate_email(email: str) -> str:
    email = _validate_string(email, "Email", 255)
    if '@' not in email or '.' not in email:
        raise ValueError("Invalid email format")
    return email.lower()


# ----------------------------------------------------------------------
# CRUD Operations
# ----------------------------------------------------------------------

def create_user(
    username: str,
    email: str,
    password_hash: str,
    full_name: Optional[str] = None
) -> User:
    """Create a new user with transaction safety"""
    if not isinstance(password_hash, str) or len(password_hash) < 8:
        raise ValueError("Valid password hash is required")

    username = _validate_string(username, "Username", 80)
    email = _validate_email(email)
    full_name = _validate_string(full_name, "Full name", 150) if full_name else None

    try:
        with db.session.begin():  # Transaction context
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,  # Never log this
                full_name=full_name
            )
            db.session.add(user)
            db.session.flush()  # Get ID without committing yet
            return user
    except IntegrityError as e:
        db.session.rollback()
        if "unique constraint" in str(e).lower():
            raise ValueError("Username or email already exists") from e
        raise
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError("Database error while creating user") from e


def get_user_by_id(user_id: int) -> Optional[User]:
    """Get user by ID"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise TypeError("user_id must be a positive integer")

    try:
        return db.session.get(User, user_id)
    except SQLAlchemyError as e:
        raise RuntimeError("Database error while fetching user") from e


def get_user_by_username(username: str) -> Optional[User]:
    """Get user by username"""
    username = _validate_string(username, "Username", 80)

    try:
        return db.session.execute(
            text("SELECT * FROM users WHERE username = :username LIMIT 1")
        ).params(username=username).scalar_one_or_none()
    except SQLAlchemyError as e:
        raise RuntimeError("Database error while fetching user by username") from e


def get_user_by_email(email: str) -> Optional[User]:
    """Get user by email"""
    email = _validate_email(email)

    try:
        return db.session.execute(
            text("SELECT * FROM users WHERE email = :email LIMIT 1")
        ).params(email=email).scalar_one_or_none()
    except SQLAlchemyError as e:
        raise RuntimeError("Database error while fetching user by email") from e


def update_user(
    user_id: int,
    full_name: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[User]:
    """Update user with transaction"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise TypeError("user_id must be a positive integer")

    try:
        with db.session.begin():
            user = db.session.get(User, user_id)
            if not user:
                return None

            if full_name is not None:
                user.full_name = _validate_string(full_name, "Full name", 150) if full_name else None

            if is_active is not None:
                if not isinstance(is_active, bool):
                    raise TypeError("is_active must be a boolean")
                user.is_active = is_active

            return user
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError("Database error while updating user") from e


def delete_user(user_id: int) -> bool:
    """Soft delete alternative: set is_active=False, or hard delete if needed"""
    if not isinstance(user_id, int) or user_id <= 0:
        raise TypeError("user_id must be a positive integer")

    try:
        with db.session.begin():
            user = db.session.get(User, user_id)
            if not user:
                return False
            user.is_active = False  # Soft delete
            return True
    except SQLAlchemyError as e:
        db.session.rollback()
        raise RuntimeError("Database error while deleting user") from e


def list_users(limit: int = 50, offset: int = 0) -> List[User]:
    """List users with pagination"""
    if not isinstance(limit, int) or limit < 1 or limit > 200:
        raise ValueError("limit must be between 1 and 200")
    if not isinstance(offset, int) or offset < 0:
        raise ValueError("offset must be non-negative")

    try:
        return db.session.execute(
            text("SELECT * FROM users WHERE is_active = true ORDER BY id LIMIT :limit OFFSET :offset")
        ).params(limit=limit, offset=offset).all()
    except SQLAlchemyError as e:
        raise RuntimeError("Database error while listing users") from e