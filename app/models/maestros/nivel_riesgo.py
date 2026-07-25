from app import db


class NivelRiesgo(db.Model):

    __tablename__ = "nivel_riesgo"

    id_nivel_riesgo = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(50),
        nullable=False
    )

    descripcion = db.Column(
        db.String(250)
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<NivelRiesgo {self.nombre}>"