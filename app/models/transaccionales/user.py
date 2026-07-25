from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime

from app import db


class User(db.Model):
    """User model for system authentication."""

    __tablename__ = 'users'

    ROLES = ('admin', 'auxiliar', 'medico')

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    rol = db.Column(
        db.String(20),
        default='auxiliar',
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    def set_password(self, password):
        """Hash and set password."""
        if password:
            self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash."""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False

    def is_admin(self):
        """Check if user is admin."""
        return self.rol == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'