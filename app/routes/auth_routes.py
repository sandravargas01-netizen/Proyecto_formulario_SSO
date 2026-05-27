from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    session,
    url_for
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

        # ADMIN
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

        # AUXILIAR
        if (
            email == "auxiliar@gmail.com"
            and
            password == "123"
        ):

            session["usuario"] = email

            session["rol"] = "auxiliar"

            return redirect(
                "/pacientes/"
            )

    return render_template(
        "auth/login.html"
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
