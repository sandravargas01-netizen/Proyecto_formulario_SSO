from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen

reportes_bp = Blueprint(
    "reportes",
    __name__,
    url_prefix="/reportes"
)


@reportes_bp.route("/")
def index():
    """Página principal de reportes"""
    
    total_empleados = Empleado.query.count()
    total_examenes = Examen.query.count()
    empleados_activos = Empleado.query.filter_by(estado="activo").count()
    
    return render_template(
        "reportes/index.html",
        total_empleados=total_empleados,
        total_examenes=total_examenes,
        empleados_activos=empleados_activos
    )


@reportes_bp.route("/empleados")
def empleados():
    """Reporte de empleados"""
    
    cedula = request.args.get("cedula", "").strip()
    estado = request.args.get("estado", "").strip()
    
    query = Empleado.query
    
    if cedula:
        query = query.filter_by(cedula=cedula)
    
    if estado:
        query = query.filter_by(estado=estado)
    
    empleados = query.all()
    
    return render_template(
        "reportes/empleados.html",
        empleados=empleados,
        cedula=cedula,
        estado=estado
    )


@reportes_bp.route("/examenes")
def examenes():
    """Reporte de exámenes"""
    
    tipo_examen = request.args.get("tipo_examen", "").strip()
    
    query = Examen.query.order_by(Examen.fecha_examen.desc())
    
    if tipo_examen:
        query = query.filter_by(tipo_examen=tipo_examen)
    
    examenes = query.all()
    
    return render_template(
        "reportes/examenes.html",
        examenes=examenes,
        tipo_examen=tipo_examen
    )
