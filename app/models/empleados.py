from app import db
from datetime import datetime


class Empleado(db.Model):

    __tablename__ = 'empleados'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(120),
        nullable=False
    )

    cedula = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    fecha_nacimiento = db.Column(
        db.String(20)
    )

    telefono = db.Column(
        db.String(20)
    )

    correo = db.Column(
        db.String(120)
    )

    eps = db.Column(
        db.String(120)
    )

    afp = db.Column(
        db.String(120)
    )

    sexo = db.Column(
        db.String(20)
    )

    cargo = db.Column(
        db.String(120)
    )

    fecha_ingreso = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    estado = db.Column(
        db.String(20),
        default='activo'
    )

    def __repr__(self):

        return f'<Empleado {self.nombre}>'