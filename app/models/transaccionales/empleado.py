from app import db
from datetime import date


class Empleado(db.Model):

    __tablename__ = "empleados"

    # ===============================
    # CLAVE PRIMARIA
    # ===============================
    id_empleado = db.Column(
        db.Integer,
        primary_key=True
    )

    # ===============================
    # INFORMACIÓN BÁSICA
    # ===============================
    fecha_actualizacion = db.Column(
        db.Date
    )

    fecha_registro = db.Column(
        db.Date,
        default=date.today,
        nullable=False
    )

    cedula = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    nombres = db.Column(
    db.String(120),
    nullable=False
    )

    apellidos = db.Column(
    db.String(120),
    nullable=False
    )
    fecha_nacimiento = db.Column(
        db.Date
    )

    sexo = db.Column(
        db.String(1)
    )

    telefono = db.Column(
        db.String(20)
    )

    correo = db.Column(
        db.String(120)
    )

    # ===============================
    # INFORMACIÓN LABORAL
    # ===============================
    fecha_ingreso = db.Column(
        db.Date
    )

    fecha_retiro = db.Column(
        db.Date
    )

    estado = db.Column(
        db.String(20),
        default="Activo"
    )

    origen_datos = db.Column(
        db.String(30),
        default="Excel"
    )

    # ===============================
    # LLAVES FORÁNEAS
    # ===============================
    id_eps = db.Column(
        db.Integer,
        db.ForeignKey("eps.id_eps")
    )

    id_afp = db.Column(
        db.Integer,
        db.ForeignKey("afp.id_afp")
    )

    id_cargo = db.Column(
        db.Integer,
        db.ForeignKey("cargo.id_cargo")
    )

    id_dependencia = db.Column(
        db.Integer,
        db.ForeignKey("dependencia.id_dependencia")
    )

    id_centro_costo = db.Column(
        db.Integer,
        db.ForeignKey("centro_costo.id_centro_costo")
    )

    id_vinculacion = db.Column(
        db.Integer,
        db.ForeignKey("vinculacion.id_vinculacion")
    )

    id_estamento = db.Column(
        db.Integer,
        db.ForeignKey("estamento.id_estamento")
    )

    # ===============================
    # RELACIONES SQLALCHEMY
    # ===============================
    eps = db.relationship(
        "EPS",
        backref="empleados"
    )

    afp = db.relationship(
        "AFP",
        backref="empleados"
    )

    cargo = db.relationship(
        "Cargo",
        backref="empleados"
    )

    dependencia = db.relationship(
        "Dependencia",
        backref="empleados"
    )

    centro_costo = db.relationship(
        "CentroCosto",
        backref="empleados"
    )

    vinculacion = db.relationship(
        "Vinculacion",
        backref="empleados"
    )

    estamento = db.relationship(
        "Estamento",
        backref="empleados"
    )

    examenes = db.relationship(
        "Examen",
        backref="empleado",
        lazy="dynamic"
    )

    # ===============================
    # REPRESENTACIÓN
    # ===============================
    def __repr__(self):
        return f"<Empleado {self.cedula} - {self.nombres}>"