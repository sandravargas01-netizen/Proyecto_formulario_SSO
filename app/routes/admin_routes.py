from flask import (
    Blueprint,
    render_template
)

from app.models.paciente import Paciente
from app.models.examen import Examen


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)


# ==========================================
# DASHBOARD
# ==========================================

@admin_bp.route("/dashboard")
def dashboard():

    # ==============================
    # CONTADORES
    # ==============================

    total_empleados = Paciente.query.count()

    total_examenes = Examen.query.count()

    activos = Paciente.query.filter_by(
        estado="activo"
    ).count()

    # ==============================
    # LISTAS
    # ==============================

    pacientes = Paciente.query.all()

    examenes = Examen.query.all()

    # ==============================
    # TEMPLATE
    # ==============================

    return render_template(

        "admin/dashboard.html",

        total_empleados=total_empleados,

        total_examenes=total_examenes,

        activos=activos,

        pacientes=pacientes,

        examenes=examenes
    )


# ==========================================
# USUARIOS
# ==========================================

@admin_bp.route("/users")
def users():

    pacientes = Paciente.query.all()

    return render_template(
        "admin/users.html",
        pacientes=pacientes
    )


# ==========================================
# REPORTES
# ==========================================

@admin_bp.route("/reports")
def reports():

    examenes = Examen.query.all()

    return render_template(
        "admin/reports.html",
        examenes=examenes
    )