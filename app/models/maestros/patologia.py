from app import db


class Patologia(db.Model):

    __tablename__ = "patologia"

    id_patologia = db.Column(
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
        return f"<Patologia {self.nombre}>"