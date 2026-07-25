from app import db


class EPS(db.Model):

    __tablename__ = "eps"

    id_eps = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(120),
        nullable=False,
        unique=True
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<EPS {self.nombre}>"