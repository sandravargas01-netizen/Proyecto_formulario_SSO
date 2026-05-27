from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for
)

from app import db

from app.models.examen import Examen


examen_bp = Blueprint(
    "examen",
    __name__,
    url_prefix="/examenes"
)


# ==========================================
# LISTAR
# ==========================================

@examen_bp.route("/")
def listar():

    examenes = Examen.query.all()

    return render_template(
        "examenes/list.html",
        examenes=examenes
    )


# ==========================================
# CREAR
# ==========================================

@examen_bp.route(
    "/crear",
    methods=["GET", "POST"]
)
def crear():

    if request.method == "POST":

        examen = Examen(

            tipo_examen=request.form["tipo_examen"],

            fecha_examen=request.form["fecha_examen"],

            tipo_contrato=request.form["tipo_contrato"]
        )

        db.session.add(examen)

        db.session.commit()

        return redirect(
            url_for("examen.listar")
        )

    return render_template(
        "examenes/crear.html"
    )