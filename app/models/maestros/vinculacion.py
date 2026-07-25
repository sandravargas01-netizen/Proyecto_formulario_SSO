from app import db


class Vinculacion(db.Model):

    __tablename__ = "vinculacion"

    id_vinculacion = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(250)
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<Vinculacion {self.nombre}>"