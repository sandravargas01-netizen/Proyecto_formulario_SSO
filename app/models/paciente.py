from app.models import db
from datetime import datetime

class Paciente(db.Model):
    """Paciente (patient) model."""
    __tablename__ = 'pacientes'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    cedula = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120))
    telefono = db.Column(db.String(20))
    fecha_ingreso = db.Column(db.DateTime, default=datetime.utcnow)
    estado = db.Column(db.String(20), default='activo', nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Paciente {self.nombre} ({self.cedula})>'