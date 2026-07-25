from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for
)

configuracion_bp = Blueprint(
    "configuracion",
    __name__,
    url_prefix="/configuracion"
)


@configuracion_bp.route("/")
def index():
    """Página principal de configuración"""
    
    return render_template("configuracion/index.html")


@configuracion_bp.route("/sistema")
def sistema():
    """Configuración del sistema"""
    
    return render_template("configuracion/sistema.html")


@configuracion_bp.route("/perfiles")
def perfiles():
    """Gestión de perfiles y roles"""
    
    return render_template("configuracion/perfiles.html")


@configuracion_bp.route("/empleados")
def empleados():
    """Acceso al componente de gestión de empleados desde configuración."""

    return redirect(url_for("empleado.listar"))
