from app import db


class Diagnostico(db.Model):

    __tablename__ = "diagnostico"

    id_diagnostico = db.Column(
        db.Integer,
        primary_key=True
    )

    codigo_cie10 = db.Column(
        db.String(10),
        nullable=False
    )

    nombre_diagnostico = db.Column(
        db.String(250),
        nullable=False
    )

    id_patologia = db.Column(
        db.Integer,
        db.ForeignKey("patologia.id_patologia")
    )

    def __repr__(self):
        return f"<Diagnostico {self.codigo_cie10}>"