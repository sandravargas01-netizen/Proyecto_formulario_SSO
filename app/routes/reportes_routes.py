from io import BytesIO

from flask import (
    Blueprint,
    abort,
    render_template,
    redirect,
    send_file,
    session,
    url_for,
    flash,
    request
)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy import func

from app import db
from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen
from app.models.transaccionales.user import User

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
    empleados_activos = Empleado.query.filter(func.lower(func.trim(Empleado.estado)) == "activo").count()
    
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
        query = query.filter(func.lower(func.trim(Empleado.estado)) == estado.lower())
    
    empleados = query.all()
    
    return render_template(
        "reportes/empleados.html",
        empleados=empleados,
        cedula=cedula,
        estado=estado
    )


@reportes_bp.route("/empleados/excel")
def empleados_excel():
    username = session.get("usuario")
    if not username:
        return redirect(url_for("auth.login"))
    user = User.query.filter_by(username=username).first()
    if not user or not user.is_active or user.rol != session.get("rol") or user.rol not in User.ROLES:
        abort(403)

    registros = (
        db.session.query(Empleado, func.count(Examen.id).label("total_examenes"))
        .outerjoin(Examen, Examen.id_empleado == Empleado.id_empleado)
        .filter(func.lower(func.trim(Empleado.estado)) == "activo")
        .group_by(Empleado.id_empleado)
        .order_by(Empleado.apellidos, Empleado.nombres, Empleado.id_empleado)
        .all()
    )
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Empleados activos"
    sheet.append(["Cédula", "Nombres", "Apellidos", "Estado", "Correo", "Total de exámenes"])
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="A90020")
    for empleado, total in registros:
        sheet.append([empleado.cedula, empleado.nombres, empleado.apellidos, empleado.estado, empleado.correo or "", total])
        for cell in sheet[sheet.max_row][:5]:
            cell.data_type = "s"
    for column, width in zip("ABCDEF", (20, 25, 25, 15, 32, 22)):
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    response = send_file(
        output, as_attachment=True, download_name="empleados_activos.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


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
