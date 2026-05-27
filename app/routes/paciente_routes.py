from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request
)

from app import db

from app.models.paciente import Paciente


paciente_bp = Blueprint(
    "paciente",
    __name__,
    url_prefix="/pacientes"
)


# ==========================================
# LISTAR
# ==========================================

@paciente_bp.route("/")
def listar():

    pacientes = Paciente.query.all()

    return render_template(
        "pacientes/list.html",
        pacientes=pacientes
    )


# ==========================================
# CREAR
# ==========================================

@paciente_bp.route("/crear", methods=["GET", "POST"])
def crear():

    if request.method == "POST":

        paciente = Paciente(

            nombre=request.form["nombre"],

            cedula=request.form["cedula"],

            fecha_nacimiento=request.form["fecha_nacimiento"],

            telefono=request.form["telefono"],

            correo=request.form["correo"],

            eps=request.form["eps"],

            afp=request.form["afp"],

            sexo=request.form["sexo"],

            cargo=request.form["cargo"]
        )

        db.session.add(paciente)

        db.session.commit()

        return redirect(
            url_for("paciente.listar")
        )

    return render_template(
        "pacientes/crear.html"
    )


# ==========================================
# DETALLE
# ==========================================

@paciente_bp.route("/<int:id>")
def detalle(id):

    paciente = Paciente.query.get_or_404(id)

    return render_template(
        "pacientes/detail.html",
        paciente=paciente
    )


# ==========================================
# ELIMINAR
# ==========================================

@paciente_bp.route(
    "/eliminar/<int:id>",
    methods=["POST"]
)
def eliminar(id):

    paciente = Paciente.query.get_or_404(id)

    db.session.delete(paciente)

    db.session.commit()

    return redirect(
        url_for("paciente.listar")
    )