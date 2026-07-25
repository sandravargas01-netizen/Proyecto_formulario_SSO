from app import db


class SistemaVigilancia(db.Model):

    __tablename__ = "sistema_vigilancia"

    id_sistema_vigilancia = db.Column(
        db.Integer,
        primary_key=True
    )

    tipo_sistema_vigilancia = db.Column(
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
        return f"<SistemaVigilancia {self.tipo_sistema_vigilancia}>"