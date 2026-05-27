from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request
)

from app import db

from app.models.empleados import Empleado


empleado_bp = Blueprint(
    "empleado",
    __name__,
    url_prefix="/empleados"
)


# ==========================================
# LISTAR
# ==========================================

@empleado_bp.route("/")
def listar():

    empleados = Empleado.query.all()

    return render_template(
        "empleados/list.html",
        empleados=empleados
    )


# ==========================================
# CREAR
# ==========================================

@empleado_bp.route("/crear", methods=["GET", "POST"])
def crear():

    if request.method == "POST":

        empleado = Empleado(

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

        db.session.add(empleado)

        db.session.commit()

        return redirect(
            url_for("empleado.listar")
        )

    return render_template(
        "empleados/crear.html"
    )


# ==========================================
# DETALLE
# ==========================================

@empleado_bp.route("/<int:id>")
def detalle(id):

    empleado = Empleado.query.get_or_404(id)

    return render_template(
        "empleados/detail.html",
        empleado=empleado
    )


# ==========================================
# ELIMINAR
# ==========================================

@empleado_bp.route(
    "/eliminar/<int:id>",
    methods=["POST"]
)
def eliminar(id):

    empleado = Empleado.query.get_or_404(id)

    db.session.delete(empleado)

    db.session.commit()

    return redirect(
        url_for("empleado.listar")
    )