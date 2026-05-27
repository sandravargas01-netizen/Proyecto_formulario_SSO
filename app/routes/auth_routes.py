from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session
)

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

        email = request.form["email"]

        password = request.form["password"]

        # =========================
        # ADMIN
        # =========================
        if (
            email == "admin@gmail.com"
            and
            password == "123"
        ):

            session["usuario"] = email

            session["rol"] = "admin"

            return redirect(
                "/admin/dashboard"
            )

        # =========================
        # AUXILIAR
        # =========================
        if (
            email == "auxiliar@gmail.com"
            and
            password == "123"
        ):

            session["usuario"] = email

            session["rol"] = "auxiliar"

            return redirect(
                "/empleados/"
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

        email = request.form["email"]

        # VALIDAR CORREOS EXISTENTES
        if (
            email == "admin@gmail.com"
            or
            email == "auxiliar@gmail.com"
        ):

            mensaje = (
                "Se envió un enlace de recuperación "
                "al correo ingresado."
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
