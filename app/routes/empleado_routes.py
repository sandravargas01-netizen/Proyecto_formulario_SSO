from app.services.catalogo_service import CatalogoService

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash
)

from app.models.transaccionales.examen import Examen
from app.services.empleado_service import EmpleadoService
from app.services.pdf_service import PDFService
import re
import os
import io
import zipfile
from flask import send_file, flash


empleado_bp = Blueprint(
    "empleado",
    __name__,
    url_prefix="/empleados"
)


# ==========================================
# LISTAR EMPLEADOS
# ==========================================

@empleado_bp.route("/")
def listar():
    
    cedula = request.args.get("cedula", "").strip()

    nombre = request.args.get("nombre", "").strip()

    estado = request.args.get("estado", "").strip()

    empleados = EmpleadoService.listar(
        cedula=cedula,
        nombre=nombre,
        estado=estado
    )

    return render_template(
        "empleados/list.html",
        empleados=empleados,
        filtros={
            "cedula": cedula,
            "nombre": nombre,
            "estado": estado,
        }
    )


# ==========================================
# CREAR EMPLEADO
# ==========================================

@empleado_bp.route("/crear", methods=["GET", "POST"])
def crear():

    if request.method == "POST":

        EmpleadoService.crear(request.form)

        flash(
            "Empleado registrado correctamente.",
            "success"
        )

        return redirect(
            url_for("empleado.listar")
        )
        
    catalogos = CatalogoService.obtener_catalogos()

    return render_template(
        "empleados/crear.html",
        **catalogos
    )


# ==========================================
# VER DETALLE
# ==========================================

@empleado_bp.route("/<int:id>")
def detalle(id):

    empleado = EmpleadoService.obtener_por_id(id)

    if not empleado:

        flash(
            "Empleado no encontrado.",
            "warning"
        )

        return redirect(
            url_for("empleado.listar")
        )

    return render_template(
        "empleados/detail.html",
        empleado=empleado
    )


@empleado_bp.route("/<int:id>/consulta-integral")
def consulta_integral(id):

    empleado = EmpleadoService.obtener_por_id(id)

    if not empleado:

        flash(
            "Empleado no encontrado.",
            "warning"
        )

        return redirect(
            url_for("empleado.listar")
        )

    examenes = Examen.query.filter_by(id_empleado=id).order_by(Examen.fecha_examen.desc()).all()

    # extract pdf filename from observaciones if present and check file existence
    uploads_dir = os.path.join(os.getcwd(), 'instance', 'uploads')
    for examen in examenes:
        examen.pdf_eps = None
        if examen.observaciones:
            m = re.search(r"Archivo PDF EPS:\s*(\S+)", examen.observaciones)
            if m:
                fname = m.group(1)
                fpath = os.path.join(uploads_dir, fname)
                if os.path.exists(fpath):
                    examen.pdf_eps = fname

    return render_template(
        "empleados/consulta_integral.html",
        empleado=empleado,
        examenes=examenes
    )


@empleado_bp.route("/<int:id>/descargar-historia")
def descargar_historia(id):
    empleado = EmpleadoService.obtener_por_id(id)

    if not empleado:
        flash(
            "Empleado no encontrado.",
            "warning"
        )
        return redirect(url_for("empleado.listar"))

    examenes = Examen.query.filter_by(id_empleado=id).order_by(Examen.fecha_examen.desc()).all()

    uploads_dir = os.path.join(os.getcwd(), 'instance', 'uploads')

    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        # add a text file with the combined history
        lines = []
        for ex in examenes:
            lines.append(f"Fecha: {ex.fecha_examen} | Tipo: {ex.tipo_examen} | Concepto: {ex.concepto_medico or ''}")
            if ex.observaciones:
                lines.append(f"Observaciones: {ex.observaciones}")
            lines.append("\n")

        zf.writestr('historia.txt', '\n'.join(lines))

        # attach any PDFs found in observaciones
        for ex in examenes:
            if ex.observaciones:
                m = re.search(r"Archivo PDF EPS:\s*(\S+)", ex.observaciones)
                if m:
                    fname = m.group(1)
                    fpath = os.path.join(uploads_dir, fname)
                    if os.path.exists(fpath):
                        zf.write(fpath, arcname=os.path.join('pdfs', fname))

    mem_zip.seek(0)
    zip_name = f"historia_{empleado.cedula or empleado.id_empleado}.zip"
    return send_file(mem_zip, mimetype='application/zip', as_attachment=True, download_name=zip_name)


@empleado_bp.route("/<int:id>/descargar-historia-pdf")
def descargar_historia_pdf(id):
    empleado = EmpleadoService.obtener_por_id(id)

    if not empleado:
        flash(
            "Empleado no encontrado.",
            "warning"
        )
        return redirect(url_for("empleado.listar"))

    examenes = Examen.query.filter_by(id_empleado=id).order_by(Examen.fecha_examen.desc()).all()

    # Generar PDF
    pdf_buffer = PDFService.generar_historia_clinica_pdf(empleado, examenes)

    pdf_name = f"historia_clinica_{empleado.cedula or empleado.id_empleado}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=pdf_name
    )

# ==========================================
# EDITAR EMPLEADO
# ==========================================

@empleado_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    empleado = EmpleadoService.obtener_por_id(id)

    if not empleado:

        flash(
            "Empleado no encontrado.",
            "warning"
        )

        return redirect(
            url_for("empleado.listar")
        )

    if request.method == "POST":

        EmpleadoService.actualizar(
            id,
            request.form
        )

        flash(
            "Empleado actualizado correctamente.",
            "success"
        )

        return redirect(
            url_for("empleado.listar")
        )

    catalogos = CatalogoService.obtener_catalogos()

    return render_template(
        "empleados/editar.html",
        empleado=empleado,
        **catalogos
    )



# ==========================================
# ELIMINAR (LÓGICO)
# ==========================================

@empleado_bp.route(
    "/eliminar/<int:id>",
    methods=["POST"]
)
def eliminar(id):

    EmpleadoService.eliminar(id)

    flash(
        "Empleado retirado correctamente.",
        "warning"
    )

    return redirect(
        url_for("empleado.listar")
    )


# ==========================================
# IMPORTAR BASE MATRIZ
# ==========================================

@empleado_bp.route("/importar", methods=["GET", "POST"])
def importar_excel():

    if request.method == "POST":

        flash(
            "La importación de la Base Matriz estará disponible en la siguiente versión.",
            "info"
        )

    return render_template(
        "empleados/importar_excel.html"
    )