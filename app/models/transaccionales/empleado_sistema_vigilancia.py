from app import db
from datetime import date


class EmpleadoSistemaVigilancia(db.Model):

    __tablename__ = "empleado_sistema_vigilancia"

    id_registro = db.Column(
        db.Integer,
        primary_key=True
    )

    id_empleado = db.Column(
        db.Integer,
        db.ForeignKey("empleados.id_empleado"),
        nullable=False
    )

    id_sistema_vigilancia = db.Column(
        db.Integer,
        db.ForeignKey("sistema_vigilancia.id_sistema_vigilancia"),
        nullable=False
    )

    fecha_asignacion = db.Column(
        db.Date,
        nullable=False
    )

    fecha_retiro = db.Column(
        db.Date
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    motivo_retiro = db.Column(
    db.String(200)
)    
        
    def __repr__(self):
        return f"<EmpleadoSistemaVigilancia {self.id_registro}>"