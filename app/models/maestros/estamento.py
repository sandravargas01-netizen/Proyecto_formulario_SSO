from app import db


class Estamento(db.Model):

    __tablename__ = "estamento"

    id_estamento = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<Estamento {self.nombre}>"