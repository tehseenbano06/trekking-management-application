"""
Run this ONCE to create the Admin account:  python seed_admin.py

The problem statement requires Admin to be pre-created, not registered
through a form. This script does that using SQLAlchemy directly, which
satisfies the "programmatically created" requirement.
"""
from werkzeug.security import generate_password_hash
from app import app
from extensions import db
from models import User

ADMIN_EMAIL = "admin@trek.com"
ADMIN_PASSWORD = "admin123"  # change this before your final submission

with app.app_context():
    db.create_all()

    existing = User.query.filter_by(email=ADMIN_EMAIL).first()
    if existing:
        print("Admin already exists:", existing.email)
    else:
        admin = User(
            name="Administrator",
            email=ADMIN_EMAIL,
            password_hash=generate_password_hash(ADMIN_PASSWORD),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin created:", ADMIN_EMAIL, "/ password:", ADMIN_PASSWORD)
