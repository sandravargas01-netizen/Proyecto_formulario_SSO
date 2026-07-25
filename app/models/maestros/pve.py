from app import db


class PVE(db.Model):

    __tablename__ = "pve"

    id_pve = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False,
        unique=True
    )

    descripcion = db.Column(
        db.String(250)
    )

    estado = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    def __repr__(self):
        return f"<PVE {self.nombre}>"