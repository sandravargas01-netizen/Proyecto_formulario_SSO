from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    flash,
    url_for
)

from app.models.transaccionales.user import User

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


# ==========================================
# LOGIN
# ==========================================

@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        password = request.form["password"]

        usuario = User.query.filter_by(email=email).first()

        if usuario and usuario.check_password(password):

            if not usuario.is_active:
                flash(
                    "El usuario está inactivo. Contacte al administrador.",
                    "warning"
                )
                return redirect(url_for("auth.login"))

            session["usuario"] = usuario.username

            session["rol"] = usuario.rol

            if usuario.rol == "admin":
                return redirect(
                    "/admin/dashboard"
                )

            return redirect(
                "/empleados/"
            )

        flash(
            "Email o contraseña incorrectos.",
            "danger"
        )

    return render_template(
        "auth/login.html"
    )


# ==========================================
# RECUPERAR CONTRASEÑA
# ==========================================

@auth_bp.route(
    "/recuperar-password",
    methods=["GET", "POST"]
)
def recuperar_password():

    mensaje = None

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        usuario = User.query.filter_by(email=email).first()

        if usuario:
            mensaje = (
                "Se envió un enlace de recuperación al correo ingresado."
            )
        else:
            mensaje = (
                "El correo no existe en el sistema."
            )

    return render_template(
        "auth/recuperar_password.html",
        mensaje=mensaje
    )


# ==========================================
# LOGOUT
# ==========================================

@auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        "/auth/login"
    )
