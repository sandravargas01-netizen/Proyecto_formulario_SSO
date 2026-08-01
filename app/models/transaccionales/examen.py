from datetime import date

from app import db


class Examen(db.Model):

    __tablename__ = "examenes"

    id = db.Column(db.Integer, primary_key=True)

    id_empleado = db.Column(
        db.Integer,
        db.ForeignKey("empleados.id_empleado")
    )

    tipo_examen = db.Column(
        db.String(120),
        nullable=False
    )

    fecha_examen = db.Column(
        db.String(10)
    )

    medico = db.Column(
        db.String(120)
    )

    ips = db.Column(
        db.String(120)
    )

    concepto_medico = db.Column(
        db.String(255)
    )

    observaciones = db.Column(
        db.Text
    )

    estado = db.Column(
        db.String(80)
    )

    concepto_de_aptitud = db.Column(
        db.String(80)
    )

    restricciones_medicas = db.Column(
        db.Text
    )

    recomendaciones_medicas = db.Column(
        db.Text
    )

    fecha_nuevo_control = db.Column(
        db.String(10)
    )

    fecha_registro = db.Column(
        db.String(10),
        default=lambda: date.today().isoformat(),
        nullable=False
    )
