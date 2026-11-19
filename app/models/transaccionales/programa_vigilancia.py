from app import db


class ProgramaVigilancia(db.Model):
    __tablename__ = "programa_vigilancia"

    id = db.Column(db.Integer, primary_key=True)
    id_empleado = db.Column(
        db.Integer, db.ForeignKey("empleados.id_empleado"), nullable=False, index=True
    )
    programa = db.Column(db.String(40), nullable=False)
    fecha_ingreso = db.Column(db.Date, nullable=False)
    dependencia = db.Column(db.String(200))
    cargo = db.Column(db.String(200))
    riesgos = db.Column(db.Text, nullable=False)
    hallazgos = db.Column(db.Text, nullable=False)
    observaciones = db.Column(db.Text)
    descripcion_soporte = db.Column(db.Text)
    responsable = db.Column(db.String(200), nullable=False)
    nombre_registrador = db.Column(db.String(200))
    id_usuario_registro = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    soporte_nombre = db.Column(db.String(180))
    soporte_pdf = db.deferred(db.Column(db.LargeBinary))
