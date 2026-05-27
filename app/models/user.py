from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from datetime import datetime

from app import db


class User(UserMixin, db.Model):
    """User model with authentication support."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        default='staff',
        nullable=False
    )

    first_name = db.Column(db.String(100))

    last_name = db.Column(db.String(100))

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

    pacientes = db.relationship(
        'Paciente',
        backref='user',
        lazy=True,
        cascade='all, delete-orphan'
    )

    def set_password(self, password):
        """Hash and set password."""

        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify password against hash."""

        return check_password_hash(
            self.password_hash,
            password
        )

    def is_admin(self):
        """Check if user is admin."""

        return self.role == 'admin'

    def __repr__(self):

        return f'<User {self.email}>'