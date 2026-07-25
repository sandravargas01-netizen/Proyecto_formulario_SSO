from app import db


class Cargo(db.Model):

    __tablename__ = "cargo"

    id_cargo = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(150),
        nullable=False
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<Cargo {self.nombre}>"