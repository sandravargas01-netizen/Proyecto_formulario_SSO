from app import db


class Examen(db.Model):

    __tablename__ = "examenes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo_examen = db.Column(
        db.String(100),
        nullable=False
    )

    fecha_examen = db.Column(
        db.String(50),
        nullable=False
    )


    id_empleado = db.Column(
        db.Integer,
        db.ForeignKey("empleados.id_empleado"),
        nullable=False
    )

    medico = db.Column(
        db.String(100),
        nullable=True
    )

    ips = db.Column(
        db.String(100),
        nullable=True
    )

    estado = db.Column(
        db.String(50),
        nullable=True
    )

    concepto_medico = db.Column(
        db.String(255),
        nullable=True
    )

    fecha_nuevo_control = db.Column(
        db.String(50),
        nullable=True
    )

    observaciones = db.Column(
        db.Text,
        nullable=True
    )

    tipo_ingreso = db.Column(
        db.String(100),
        nullable=True
    )

    tipo_contrato = db.Column(
        db.String(100),
        nullable=True
    )

    concepto_de_aptitud = db.Column(
        db.String(255),
        nullable=True
    )

    restricciones_medicas = db.Column(
        db.Text,
        nullable=True
    )

    recomendaciones_medicas = db.Column(
        db.Text,
        nullable=True
    )

    def __repr__(self):

        return f"<Examen {self.tipo_examen}>"