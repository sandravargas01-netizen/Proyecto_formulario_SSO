from app import db


class Periodicidad(db.Model):

    __tablename__ = "periodicidad"

    id_periodicidad = db.Column(
        db.Integer,
        primary_key=True
    )

    meses = db.Column(
        db.Integer,
        nullable=False
    )

    descripcion = db.Column(
        db.String(100)
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<Periodicidad {self.meses}>"