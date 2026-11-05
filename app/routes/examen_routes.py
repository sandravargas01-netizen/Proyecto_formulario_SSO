from flask import (
    Blueprint,
    current_app,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
    send_file,
    flash
)
import json
import os
from datetime import date
from werkzeug.utils import secure_filename

from app import db

from app.models.transaccionales.examen import Examen
from app.models.transaccionales.empleado import Empleado
from app.models.maestros.eps import EPS
from app.models.maestros.afp import AFP
from app.services.pdf_service import PDFService
from app.services.empleado_service import EmpleadoService


examen_bp = Blueprint(
    "examen",
    __name__,
    url_prefix="/examenes"
)


NOVEDAD_LABELS = {
    "valoracion_ocupacional": "Valoración ocupacional",
    "periodico_ocupacional": "Examen periódico ocupacional",
    "pre_ingreso": "Examen de pre-ingreso",
    "ingreso": "Examen de ingreso",
    "egreso": "Examen de egreso",
    "reintegro": "Reintegro",
    "retorno_laboral": "Retorno laboral",
    "post_incapacidad": "Post incapacidad",
    "cambio_cargo": "Cambio de cargo",
    "cambio_ocupacion": "Examen por cambio de ocupación",
    "seguimiento": "Examen de seguimiento",
    "sistema_vigilancia": "Sistema de vigilancia epidemiológica",
    "valoracion_psicosocial": "Valoración de psicología ocupacional",
    "terapia_ocupacional": "Valoración de terapia ocupacional",
    "fisioterapia": "Valoración de fisioterapia ocupacional",
    "certificacion_alto_riesgo": "Certificación de actividad de alto riesgo",
    "integrador_multidisciplinario": "Concepto multidisciplinario integrador",
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

    for line in detalle.splitlines():
        if line.startswith("HCO_DATA:"):
            try:
                metadata["hco_data"] = json.loads(line[len("HCO_DATA:"):].strip())
            except json.JSONDecodeError:
                metadata["hco_data"] = {}
            break

    field_map = {
        "Tipo de examen": "tipo_novedad",
        "Tipo de valoración": "tipo_valoracion",
        "Tipos de examen": "tipos_novedad",
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

    if metadata.get("tipos_novedad"):
        metadata["tipos_novedad"] = [
            tipo.strip()
            for tipo in metadata["tipos_novedad"].split(",")
            if tipo.strip()
        ]

    tipo_novedad = metadata.get("tipo_novedad")

    if not tipo_novedad and metadata.get("tipos_novedad"):
        tipo_novedad = metadata["tipos_novedad"][0]
        metadata["tipo_novedad"] = tipo_novedad

    if tipo_novedad:
        metadata["tipo_novedad_label"] = NOVEDAD_LABELS.get(
            tipo_novedad,
            tipo_novedad.replace("_", " ").title()
        )

    tipo_valoracion = metadata.get("tipo_valoracion")
    if tipo_valoracion:
        metadata["tipo_valoracion_label"] = NOVEDAD_LABELS.get(
            tipo_valoracion,
            tipo_valoracion.replace("_", " ").title()
        )

    if metadata.get("tipos_novedad"):
        metadata["tipos_novedad_labels"] = [
            NOVEDAD_LABELS.get(tipo, tipo.replace("_", " ").title())
            for tipo in metadata["tipos_novedad"]
        ]

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


def _procesar_formulario_examen(empleado):
    """Procesa el formulario de examen/HCO y retorna los campos calculados
    para construir o actualizar un registro ``Examen``. También actualiza los
    datos personales del ``empleado`` recibido. Reutilizado por las rutas de
    creación y edición de examenes para evitar duplicar la lógica."""

    tipos_novedad = [
        value.strip()
        for value in request.form.getlist('tipo_novedad')
        if value and value.strip()
    ]

    if not tipos_novedad:
        tipo_unico = (request.form.get('tipo_novedad') or '').strip()
        if tipo_unico:
            tipos_novedad = [tipo_unico]

    tipo_novedad = tipos_novedad[0] if tipos_novedad else None
    tipo_examen = (request.form.get('tipo_examen') or '').strip()
    tipo_valoracion = (request.form.get('tipo_valoracion') or '').strip()
    fecha_novedad = request.form.get('fecha_novedad') or date.today().isoformat()
    estado_novedad = request.form.get('estado_novedad') or 'pendiente'
    riesgos = request.form.getlist('riesgo[]') or request.form.getlist('riesgo')
    especialidad_eps = request.form.get('especialidad_eps')
    observaciones_eps = request.form.get('observaciones_eps')
    descripcion_otro = request.form.get('descripcion_otro')

    # handle pdf upload
    pdf_filename = None
    upload = request.files.get('pdf_eps')
    if upload and upload.filename:
        filename = secure_filename(upload.filename)
        uploads_dir = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(uploads_dir, exist_ok=True)
        save_path = os.path.join(uploads_dir, filename)
        upload.save(save_path)
        pdf_filename = filename

    # Consolidate extra fields into observaciones to avoid DB schema changes
    extra = []
    if tipo_novedad:
        extra.append(f"Tipo de examen: {tipo_novedad}")
    if tipo_examen:
        extra.append(f"Tipo de examen: {tipo_examen}")
    if tipo_valoracion:
        extra.append(f"Tipo de valoración: {tipo_valoracion}")
    if tipos_novedad:
        extra.append(f"Tipos de examen: {','.join(tipos_novedad)}")
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

    def first_form_value(*keys):
        for key in keys:
            value = (request.form.get(key) or '').strip()
            if value:
                return value
        return None

    personal_data = {
        "ciudad_nacimiento": first_form_value("hc_ciudad_nacimiento", "hco_med_ciudad_nacimiento"),
        "ciudad_residencia": first_form_value("hc_ciudad_residencia", "hco_med_ciudad_residencia"),
        "sexo": first_form_value("hc_sexo", "hco_med_sexo"),
        "escolaridad": first_form_value("hc_escolaridad", "hco_med_escolaridad"),
        "estado_civil": first_form_value("hc_estado_civil", "hco_med_estado_civil"),
        "direccion": first_form_value("hc_direccion", "hco_med_direccion"),
        "arl": first_form_value("hc_arl", "hco_med_arl"),
        "telefono": first_form_value("hc_telefono_contacto", "hco_med_telefono"),
    }
    fecha_nacimiento = first_form_value("hc_fecha_nacimiento", "hco_med_fecha_nacimiento")
    if fecha_nacimiento:
        personal_data["fecha_nacimiento"] = EmpleadoService.convertir_fecha(fecha_nacimiento)

    for attribute, value in personal_data.items():
        if value:
            setattr(empleado, attribute, value)

    for form_key, model, attribute in (
        ("eps", EPS, "id_eps"),
        ("hc_eps", EPS, "id_eps"),
        ("hco_med_eps", EPS, "id_eps"),
        ("hc_afp", AFP, "id_afp"),
        ("hco_med_afp", AFP, "id_afp"),
    ):
        value = (request.form.get(form_key) or '').strip()
        if not value:
            continue
        catalogo = model.query.filter(db.func.lower(model.nombre) == value.lower()).first()
        if catalogo:
            setattr(empleado, attribute, catalogo.id_eps if model is EPS else catalogo.id_afp)

    hco_data = {}
    for key, values in request.form.to_dict(flat=False).items():
        if not key.startswith("hco_"):
            continue

        cleaned_values = [value.strip() for value in values if value.strip()]
        if not cleaned_values:
            continue

        hco_data[key] = cleaned_values if len(cleaned_values) > 1 else cleaned_values[0]

    if hco_data:
        extra.append(f"HCO_DATA: {json.dumps(hco_data, ensure_ascii=True)}")

    base_observ = request.form.get('observaciones') or ''
    combined_observ = base_observ
    if extra:
        combined_observ = combined_observ + "\n---\n" + "\n".join(extra)

    return {
        "tipo_examen": tipo_examen or tipo_novedad or 'NOVEDAD',
        # El campo "Fecha de examen" del formulario de HCO se envía como
        # "fecha_examen"; se le da prioridad sobre "fecha_novedad" (usado por
        # otros formularios/novedades) para que el PDF muestre la fecha
        # realmente diligenciada en vez de la fecha del día por defecto.
        "fecha_examen": request.form.get('fecha_examen') or fecha_novedad or '',
        "medico": (
            request.form.get('medico')
            or request.form.get('medico_evaluador')
            or request.form.get('post_incapacidad_medico')
        ),
        "ips": request.form.get('ips') or request.form.get('ips_proveedora'),
        "estado": request.form.get('estado') or estado_novedad,
        # El formulario de HCO no tiene un campo "concepto_medico" propio:
        # la selección se hace en "Concepto médico de aptitud" (hco_med_concepto),
        # así que se usa como respaldo para que el PDF no muestre "N/A".
        "concepto_medico": request.form.get('concepto_medico') or request.form.get('hco_med_concepto'),
        "fecha_nuevo_control": request.form.get('fecha_nuevo_control'),
        "observaciones": combined_observ,
        "concepto_de_aptitud": _normalize_concepto_aptitud(
            request.form.get('concepto_de_aptitud') or request.form.get('concepto_medico')
        ),
        "restricciones_medicas": request.form.get('restricciones_medicas') or request.form.get('restricciones'),
        "recomendaciones_medicas": request.form.get('recomendaciones_medicas') or request.form.get('recomendaciones'),
        "requiere_seguimiento": request.form.get('requiere_seguimiento') == 'true',
        "fecha_nuevo_seguimiento": request.form.get('fecha_nuevo_seguimiento'),
        "profesional_encargado_seguimiento": request.form.get('profesional_encargado_seguimiento'),
        "observaciones_seguimiento": request.form.get('observaciones_seguimiento'),
        "post_incapacidad_medico": request.form.get('post_incapacidad_medico'),
    }


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
# CREAR (ruta independiente de empleado)
# ==========================================
# Todo examen pertenece obligatoriamente a un empleado (Examen.id_empleado es
# NOT NULL), y el formulario "examenes/crear.html" solo funciona correctamente
# cuando se conoce el empleado (datos personales, panelMap, etc.). Por lo tanto
# esta ruta no crea el examen directamente: redirige al listado de empleados
# para que el usuario elija el empleado y continúe en "crear_para_empleado".
@examen_bp.route(
    "/crear",
    methods=["GET", "POST"]
)
def crear():

    flash(
        "Seleccione un empleado para registrar el examen ocupacional.",
        "info"
    )

    return redirect(
        url_for("empleado.listar")
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

    tipo_novedad_list = novedad_metadata.get("tipos_novedad") or []
    if not tipo_novedad_list:
        tipo_unico = novedad_metadata.get("tipo_novedad") or examen.tipo_examen
        tipo_novedad_list = [tipo_unico] if tipo_unico else []

    tipo_novedad = tipo_novedad_list[0] if tipo_novedad_list else None
    tipo_novedad_labels = [
        NOVEDAD_LABELS.get(tipo, tipo.replace("_", " ").title())
        for tipo in tipo_novedad_list
    ]
    tipo_novedad_label = ", ".join(tipo_novedad_labels) if tipo_novedad_labels else "No registrado"

    return render_template(
        "examenes/detail.html",
        examen=examen,
        empleado=empleado,
        observaciones_generales=observaciones_generales,
        novedad_metadata=novedad_metadata,
        tipo_novedad=tipo_novedad,
        tipo_novedad_list=tipo_novedad_list,
        tipo_novedad_labels=tipo_novedad_labels,
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

        campos = _procesar_formulario_examen(empleado)

        examen = Examen(
            id_empleado=empleado.id_empleado,
            **campos
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


@examen_bp.route(
    "/<int:id>/editar",
    methods=["GET", "POST"]
)
def editar(id):

    examen = Examen.query.get(id)

    if not examen:
        flash("El examen no existe o ya fue eliminado.", "warning")
        return redirect(url_for("examen.listar"))

    empleado = Empleado.query.get(examen.id_empleado)

    if not empleado:
        return redirect(url_for("examen.listar"))

    if request.method == "POST":

        campos = _procesar_formulario_examen(empleado)

        for attribute, value in campos.items():
            setattr(examen, attribute, value)

        db.session.commit()

        flash("Examen actualizado correctamente.", "success")

        return redirect(
            url_for("examen.detalle", id=examen.id)
        )

    observacion_general, metadata = _parse_novedad_metadata(examen.observaciones)
    hco_data_existente = metadata.get("hco_data", {})

    datos_basicos = {
        "tipo_examen": examen.tipo_examen,
        "tipo_novedad": metadata.get("tipo_novedad"),
        "tipo_valoracion": metadata.get("tipo_valoracion"),
        "estado_novedad": metadata.get("estado_novedad"),
        "medico": examen.medico,
        "medico_evaluador": examen.medico,
        "ips": examen.ips,
        "ips_proveedora": examen.ips,
        "estado": examen.estado,
        "concepto_medico": examen.concepto_medico,
        "fecha_nuevo_control": examen.fecha_nuevo_control,
        "concepto_de_aptitud": examen.concepto_de_aptitud,
        "restricciones_medicas": examen.restricciones_medicas,
        "restricciones": examen.restricciones_medicas,
        "recomendaciones_medicas": examen.recomendaciones_medicas,
        "recomendaciones": examen.recomendaciones_medicas,
        "observaciones": observacion_general,
        "fecha_novedad": examen.fecha_examen,
        "fecha_examen": examen.fecha_examen,
        "especialidad_eps": metadata.get("especialidad_eps"),
        "observaciones_eps": metadata.get("observaciones_eps"),
        "descripcion_otro": metadata.get("descripcion_otro"),
    }

    datos_prefill = dict(hco_data_existente)
    datos_prefill.update({
        key: value for key, value in datos_basicos.items()
        if value not in (None, '')
    })
    if metadata.get("riesgos"):
        datos_prefill["riesgo[]"] = metadata["riesgos"]

    return render_template(
        "examenes/crear.html",
        empleado=empleado,
        examen=examen,
        is_edit=True,
        prefill_json=json.dumps(datos_prefill, ensure_ascii=True)
    )


@examen_bp.route(
    "/<int:id>/eliminar",
    methods=["POST"]
)
def eliminar(id):

    examen = Examen.query.get(id)

    if not examen:
        flash("El examen no existe o ya fue eliminado.", "warning")
        return redirect(url_for("examen.listar"))

    empleado_id = examen.id_empleado

    db.session.delete(examen)
    db.session.commit()

    flash("Examen eliminado correctamente.", "success")

    if empleado_id:
        return redirect(
            url_for("empleado.consulta_integral", id=empleado_id, _anchor="examenes-ocupacionales")
        )

    return redirect(url_for("examen.listar"))


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
    uploads_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(uploads_dir, filename, as_attachment=True)