from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for
)

from app.forms.login_form import LoginForm

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        return redirect(url_for("paciente.listar"))

    return render_template(
        "auth/login.html",
        form=form
    )
