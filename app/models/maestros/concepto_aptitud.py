from app import db


class Concepto(db.Model):

    __tablename__ = "concepto"

    id_concepto = db.Column(
        db.Integer,
        primary_key=True
    )

    nombre = db.Column(
        db.String(100),
        nullable=False
    )

    descripcion = db.Column(
        db.String(250)
    )

    estado = db.Column(
        db.Boolean,
        default=True
    )

    def __repr__(self):
        return f"<Concepto {self.nombre}>"