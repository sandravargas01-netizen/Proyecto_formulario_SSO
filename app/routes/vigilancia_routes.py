from datetime import date
from functools import wraps
from io import BytesIO

from flask import (
    Blueprint, abort, flash, g, redirect, render_template, request,
    send_file, session, url_for,
)
from flask_wtf.csrf import generate_csrf, validate_csrf
from werkzeug.utils import secure_filename
from wtforms.validators import ValidationError

from app import db
from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.programa_vigilancia import ProgramaVigilancia
from app.models.transaccionales.user import User


vigilancia_bp = Blueprint("vigilancia", __name__, url_prefix="/vigilancia")

PROGRAMAS = {
    "auditivo": "Riesgo auditivo",
    "radiacion": "Riesgo por radiación",
    "voz": "Riesgo cuidado de la voz",
    "quimico": "Riesgo químico",
    "biomecanico": "Riesgo biomecánico - osteomuscular",
    "biologico": "Riesgo biológico",
    "psicosocial": "Riesgo psicosocial",
}
MAX_PDF_BYTES = 5 * 1024 * 1024


def administrador_requerido(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        username = session.get("usuario")
        if not username:
            return redirect(url_for("auth.login"))
        user = User.query.filter_by(username=username).first()
        if not user or not user.is_active or user.rol != "admin" or session.get("rol") != "admin":
            abort(403)
        g.vigilancia_usuario = user
        return view(*args, **kwargs)
    return wrapped


@vigilancia_bp.after_request
def no_guardar_en_cache(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@vigilancia_bp.route("/empleados/<int:empleado_id>")
@administrador_requerido
def programas(empleado_id):
    empleado = db.get_or_404(Empleado, empleado_id)
    registros = (
        ProgramaVigilancia.query.filter_by(id_empleado=empleado_id)
        .order_by(ProgramaVigilancia.fecha_ingreso.desc(), ProgramaVigilancia.id.desc())
        .all()
    )
    return render_template(
        "vigilancia/programas.html", empleado=empleado,
        programas=PROGRAMAS, registros=registros,
    )


@vigilancia_bp.route("/empleados/<int:empleado_id>/<programa>/nuevo", methods=["GET", "POST"])
@administrador_requerido
def asignar(empleado_id, programa):
    empleado = db.get_or_404(Empleado, empleado_id)
    if programa not in PROGRAMAS:
        abort(404)

    values = {
        "dependencia": empleado.dependencia.nombre if empleado.dependencia else "",
        "cargo": empleado.cargo.nombre if empleado.cargo else "",
    }
    errors = []
    if request.method == "POST":
        if request.content_length is not None and request.content_length > MAX_PDF_BYTES + 256 * 1024:
            abort(413, description="El soporte y los datos del formulario superan el tamaño permitido.")

        values = {name: request.form.get(name, "").strip() for name in (
            "fecha_ingreso", "dependencia", "cargo", "riesgos", "hallazgos",
            "observaciones", "descripcion_soporte", "responsable", "nombre_registrador"
        )}
        try:
            validate_csrf(request.form.get("csrf_token"))
        except ValidationError:
            errors.append("La sesión del formulario ha vencido. Vuelve a intentarlo.")

        try:
            fecha = date.fromisoformat(values["fecha_ingreso"])
            if fecha.isoformat() != values["fecha_ingreso"]:
                raise ValueError
        except ValueError:
            fecha = None
            errors.append("Ingresa una fecha de ingreso válida.")

        for field, label in (
            ("riesgos", "Los riesgos identificados"),
            ("hallazgos", "Los hallazgos"),
            ("responsable", "El responsable del programa"),
        ):
            if not values[field]:
                errors.append(f"{label} son obligatorios." if field != "responsable" else f"{label} es obligatorio.")
        if len(values["responsable"]) > 200:
            errors.append("El responsable no puede superar 200 caracteres.")
        if len(values["nombre_registrador"]) > 200:
            errors.append("El nombre de quien diligencia no puede superar 200 caracteres.")
        if any(len(values[field]) > 200 for field in ("dependencia", "cargo")):
            errors.append("La dependencia y el cargo no pueden superar 200 caracteres.")
        if any(len(values[field]) > 10000 for field in ("riesgos", "hallazgos", "observaciones", "descripcion_soporte")):
            errors.append("Los campos de texto no pueden superar 10.000 caracteres.")

        soporte_nombre = None
        soporte_pdf = None
        upload = request.files.get("soporte_pdf")
        if upload and upload.filename:
            if not upload.filename.lower().endswith(".pdf"):
                errors.append("El soporte médico debe ser un archivo PDF.")
            else:
                soporte_pdf = upload.stream.read(MAX_PDF_BYTES + 1)
                if len(soporte_pdf) > MAX_PDF_BYTES:
                    errors.append("El soporte médico no puede superar 5 MB.")
                elif not soporte_pdf.startswith(b"%PDF-"):
                    errors.append("El archivo seleccionado no es un PDF válido.")
                else:
                    soporte_nombre = (secure_filename(upload.filename[:-4])[:176] or "soporte") + ".pdf"

        if not errors and fecha is not None:
            registro = ProgramaVigilancia(
                id_empleado=empleado_id, programa=programa, fecha_ingreso=fecha,
                dependencia=values["dependencia"] or None, cargo=values["cargo"] or None,
                riesgos=values["riesgos"], hallazgos=values["hallazgos"],
                observaciones=values["observaciones"] or None,
                descripcion_soporte=values["descripcion_soporte"] or None,
                responsable=values["responsable"], nombre_registrador=values["nombre_registrador"] or None,
                id_usuario_registro=g.vigilancia_usuario.id,
                soporte_nombre=soporte_nombre, soporte_pdf=soporte_pdf,
            )
            db.session.add(registro)
            db.session.commit()
            flash("Programa de vigilancia registrado correctamente.", "success")
            return redirect(url_for("vigilancia.programas", empleado_id=empleado_id))

    return render_template(
        "vigilancia/asignar.html", empleado=empleado, programa=programa,
        nombre_programa=PROGRAMAS[programa], values=values, errors=errors,
        csrf_token=generate_csrf(),
    ), 400 if errors else 200


@vigilancia_bp.route("/soportes/<int:registro_id>")
@administrador_requerido
def soporte(registro_id):
    registro = db.get_or_404(ProgramaVigilancia, registro_id)
    if registro.soporte_pdf is None or not registro.soporte_nombre:
        abort(404)
    return send_file(
        BytesIO(registro.soporte_pdf), mimetype="application/pdf",
        as_attachment=True, download_name=registro.soporte_nombre,
    )