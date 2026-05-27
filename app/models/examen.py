from app import db


class Examen(db.Model):

    __tablename__ = "examenes"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo_examen = db.Column(
        db.String(100),
        nullable=False
    )

    fecha_examen = db.Column(
        db.String(50),
        nullable=False
    )

    tipo_contrato = db.Column(
        db.String(100),
        nullable=False
    )

    def __repr__(self):

        return f"<Examen {self.tipo_examen}>"