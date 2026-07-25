from app import db


class CentroCosto(db.Model):

    __tablename__ = "centro_costo"

    id_centro_costo = db.Column(
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
        return f"<CentroCosto {self.nombre}>"