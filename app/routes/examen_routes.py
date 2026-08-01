from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    send_file
)
import os
from werkzeug.utils import secure_filename
import os

from app import db

from app.models.transaccionales.examen import Examen
from app.models.transaccionales.empleado import Empleado
from app.services.pdf_service import PDFService


examen_bp = Blueprint(
    "examen",
    __name__,
    url_prefix="/examenes"
)


NOVEDAD_LABELS = {
    "periodico_ocupacional": "Examen periódico ocupacional",
    "ingreso": "Examen de ingreso",
    "egreso": "Examen de egreso",
    "reintegro": "Reintegro",
    "post_incapacidad": "Post incapacidad",
    "cambio_cargo": "Cambio de cargo",
    "sistema_vigilancia": "Sistema de vigilancia epidemiológica",
    "solicitado_eps": "Solicitado por la EPS",
    "otro": "Otro"
}


def _parse_novedad_metadata(observaciones):

    if not observaciones:
        return "", {}

    observacion_general, separador, detalle = observaciones.partition("\n---\n")

    if not separador:
        return observaciones.strip(), {}

    metadata = {}

    field_map = {
        "Tipo de novedad": "tipo_novedad",
        "Estado novedad": "estado_novedad",
        "Riesgos": "riesgos",
        "Especialidad EPS": "especialidad_eps",
        "Observaciones EPS": "observaciones_eps",
        "Descripcion otro": "descripcion_otro",
        "Archivo PDF EPS": "archivo_pdf_eps"
    }

    for line in detalle.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        mapped_key = field_map.get(key.strip())

        if mapped_key:
            metadata[mapped_key] = value.strip()

    if metadata.get("riesgos"):
        metadata["riesgos"] = [
            riesgo.strip()
            for riesgo in metadata["riesgos"].split(",")
            if riesgo.strip()
        ]

    tipo_novedad = metadata.get("tipo_novedad")

    if tipo_novedad:
        metadata["tipo_novedad_label"] = NOVEDAD_LABELS.get(
            tipo_novedad,
            tipo_novedad.replace("_", " ").title()
        )

    return observacion_general.strip(), metadata


def _normalize_concepto_aptitud(value):

    if not value:
        return value

    concept_map = {
        "Apto": "apto",
        "Apto con restricciones": "apto_con_restricciones",
        "No apto": "no_apto",
        "Pendiente resultado": "pendiente"
    }

    return concept_map.get(value, value)


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

            medico=request.form.get("medico"),

            ips=request.form.get("ips"),

            concepto_medico=request.form.get("concepto_medico"),

            observaciones=request.form.get("observaciones")
        )

        db.session.add(examen)

        db.session.commit()

        return redirect(
            url_for("examen.listar")
        )

    return render_template(
        "examenes/crear.html"
    )


@examen_bp.route("/<int:id>")
def detalle(id):

    examen = Examen.query.get(id)

    if not examen:
        return redirect(
            url_for("examen.listar")
        )

    empleado = Empleado.query.get(examen.id_empleado)
    observaciones_generales, novedad_metadata = _parse_novedad_metadata(
        examen.observaciones
    )

    tipo_novedad = novedad_metadata.get("tipo_novedad") or examen.tipo_examen
    tipo_novedad_label = NOVEDAD_LABELS.get(
        tipo_novedad,
        tipo_novedad.replace("_", " ").title()
    ) if tipo_novedad else "No registrado"

    return render_template(
        "examenes/detail.html",
        examen=examen,
        empleado=empleado,
        observaciones_generales=observaciones_generales,
        novedad_metadata=novedad_metadata,
        tipo_novedad=tipo_novedad,
        tipo_novedad_label=tipo_novedad_label
    )


@examen_bp.route(
    "/crear/<int:empleado_id>",
    methods=["GET", "POST"]
)
def crear_para_empleado(empleado_id):

    empleado = Empleado.query.get(empleado_id)

    if not empleado:
        return redirect(
            url_for("empleado.listar")
        )

    if request.method == "POST":

        # map form fields to model
        tipo_novedad = request.form.get('tipo_novedad')
        fecha_novedad = request.form.get('fecha_novedad')
        estado_novedad = request.form.get('estado_novedad')
        riesgos = request.form.getlist('riesgo[]') or request.form.getlist('riesgo')
        especialidad_eps = request.form.get('especialidad_eps')
        observaciones_eps = request.form.get('observaciones_eps')
        descripcion_otro = request.form.get('descripcion_otro')

        # handle pdf upload
        pdf_filename = None
        upload = request.files.get('pdf_eps')
        if upload and upload.filename:
            filename = secure_filename(upload.filename)
            uploads_dir = os.path.join(os.getcwd(), 'instance', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            save_path = os.path.join(uploads_dir, filename)
            upload.save(save_path)
            pdf_filename = filename

        # Consolidate extra fields into observaciones to avoid DB schema changes
        extra = []
        if tipo_novedad:
            extra.append(f"Tipo de novedad: {tipo_novedad}")
        if estado_novedad:
            extra.append(f"Estado novedad: {estado_novedad}")
        if riesgos:
            extra.append(f"Riesgos: {','.join(riesgos)}")
        if especialidad_eps:
            extra.append(f"Especialidad EPS: {especialidad_eps}")
        if observaciones_eps:
            extra.append(f"Observaciones EPS: {observaciones_eps}")
        if descripcion_otro:
            extra.append(f"Descripcion otro: {descripcion_otro}")
        if pdf_filename:
            extra.append(f"Archivo PDF EPS: {pdf_filename}")

        base_observ = request.form.get('observaciones') or ''
        combined_observ = base_observ
        if extra:
            combined_observ = combined_observ + "\n---\n" + "\n".join(extra)

        examen = Examen(
            tipo_examen=tipo_novedad or request.form.get('tipo_examen') or 'NOVEDAD',
            fecha_examen=fecha_novedad or request.form.get('fecha_examen') or '',
            medico=request.form.get('medico') or request.form.get('medico_evaluador'),
            ips=request.form.get('ips') or request.form.get('ips_proveedora'),
            estado=request.form.get('estado') or estado_novedad,
            concepto_medico=request.form.get('concepto_medico'),
            fecha_nuevo_control=request.form.get('fecha_nuevo_control'),
            observaciones=combined_observ,
            tipo_ingreso=request.form.get('tipo_ingreso'),
            tipo_contrato=request.form.get('tipo_contrato'),
            concepto_de_aptitud=_normalize_concepto_aptitud(
                request.form.get('concepto_de_aptitud') or request.form.get('concepto_medico')
            ),
            restricciones_medicas=request.form.get('restricciones_medicas') or request.form.get('restricciones'),
            recomendaciones_medicas=request.form.get('recomendaciones_medicas') or request.form.get('recomendaciones'),
            id_empleado=empleado.id_empleado
        )

        db.session.add(examen)

        db.session.commit()

        return redirect(
            url_for("empleado.consulta_integral", id=empleado.id_empleado, _anchor="examenes-ocupacionales")
        )

    return render_template(
        "examenes/crear.html",
        empleado=empleado
    )


@examen_bp.route('/<int:id>/descargar-pdf')
def descargar_examen_pdf(id):
    examen = Examen.query.get(id)
    
    if not examen:
        return redirect(url_for("examen.listar"))
    
    empleado = Empleado.query.get(examen.id_empleado)
    
    if not empleado:
        return redirect(url_for("examen.listar"))
    
    # Generar PDF
    pdf_buffer = PDFService.generar_examen_pdf(examen, empleado)
    
    pdf_name = f"examen_{empleado.cedula or empleado.id_empleado}_{examen.fecha_examen or examen.id}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=pdf_name
    )


@examen_bp.route('/<int:id>/pdf')
def ver_examen_pdf(id):
    examen = Examen.query.get(id)

    if not examen:
        return redirect(url_for("examen.listar"))

    empleado = Empleado.query.get(examen.id_empleado)

    if not empleado:
        return redirect(url_for("examen.listar"))

    pdf_buffer = PDFService.generar_examen_pdf(examen, empleado)
    pdf_name = f"examen_{empleado.cedula or empleado.id_empleado}_{examen.fecha_examen or examen.id}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=pdf_name
    )


@examen_bp.route('/pdf/<path:filename>')
def pdf_file(filename):
    uploads_dir = os.path.join(os.getcwd(), 'instance', 'uploads')
    return send_from_directory(uploads_dir, filename, as_attachment=True)