from flask import (
    Blueprint,
    render_template
)

from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen


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

    total_empleados = Empleado.query.count()

    total_examenes = Examen.query.count()

    activos = Empleado.query.filter_by(
        estado="activo"
    ).count()

    empleados = Empleado.query.all()

    examenes = Examen.query.all()

    return render_template(

        "dashboard/dashboard.html",

        total_empleados=total_empleados,

        total_examenes=total_examenes,

        activos=activos,

        empleados=empleados,

        examenes=examenes
    )


# ==========================================
# EMPLEADOS
# ==========================================

@admin_bp.route("/users")
def users():

    empleados = Empleado.query.all()

    return render_template(
        "admin/users.html",
        empleados=empleados
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