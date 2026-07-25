from app import db


class AFP(db.Model):

    __tablename__ = "afp"

    id_afp = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False,
        unique=True
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<AFP {self.nombre}>"