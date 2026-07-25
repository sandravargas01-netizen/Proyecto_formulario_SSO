from app import db


class Dependencia(db.Model):

    __tablename__ = "dependencia"

    id_dependencia = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<Dependencia {self.nombre}>"