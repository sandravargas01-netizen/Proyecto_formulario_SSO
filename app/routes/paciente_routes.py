from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request
)

from app import db

from app.models.paciente import Paciente

from app.forms.paciente_form import PacienteForm


paciente_bp = Blueprint(
    "paciente",
    __name__,
    url_prefix="/pacientes"
)


# LISTAR
@paciente_bp.route("/")
def listar():

    pacientes = Paciente.query.all()

    return render_template(
        "pacientes/list.html",
        pacientes=pacientes
    )


# CREAR
@paciente_bp.route("/crear", methods=["GET", "POST"])
def crear():

    form = PacienteForm()

    if form.validate_on_submit():

        paciente = Paciente(
            nombres=form.nombres.data,
            apellidos=form.apellidos.data,
            documento=form.documento.data,
            edad=form.edad.data,
            telefono=form.telefono.data,
            correo=form.correo.data
        )

        db.session.add(paciente)
        db.session.commit()

        return redirect(url_for("paciente.listar"))

    return render_template(
        "pacientes/crear.html",
        form=form
    )


# DETALLE
@paciente_bp.route("/<int:id>")
def detalle(id):

    paciente = Paciente.query.get_or_404(id)

    return render_template(
        "pacientes/detail.html",
        paciente=paciente
    )


# EDITAR
@paciente_bp.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):

    paciente = Paciente.query.get_or_404(id)

    form = PacienteForm(obj=paciente)

    if form.validate_on_submit():

        paciente.nombres = form.nombres.data
        paciente.apellidos = form.apellidos.data
        paciente.documento = form.documento.data
        paciente.edad = form.edad.data
        paciente.telefono = form.telefono.data
        paciente.correo = form.correo.data

        db.session.commit()

        return redirect(url_for("paciente.listar"))

    return render_template(
        "pacientes/form.html",
        form=form,
        editar=True
    )


# ELIMINAR
@paciente_bp.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):

    paciente = Paciente.query.get_or_404(id)

    db.session.delete(paciente)

    db.session.commit()

    return redirect(url_for("paciente.listar"))