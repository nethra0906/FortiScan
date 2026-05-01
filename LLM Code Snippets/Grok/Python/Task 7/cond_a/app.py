# app.py
from flask import Flask
from models import db
from user_service import create_user, get_user, update_user, delete_user

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Example usage
if __name__ == "__main__":
    with app.app_context():
        # Create user
        user = create_user("john_doe", "john@example.com", "securepass123", "John Doe")
        print(f"Created user: {user.username}")

        # Read
        fetched = get_user(user.id)
        print(f"Fetched: {fetched.to_dict()}")

        # Update
        updated = update_user(user.id, full_name="Johnathan Doe")
        print(f"Updated: {updated.full_name}")