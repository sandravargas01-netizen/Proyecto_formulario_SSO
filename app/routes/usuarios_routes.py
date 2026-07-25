from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from app.models.transaccionales.user import User
from app import db

usuarios_bp = Blueprint(
    "usuarios",
    __name__,
    url_prefix="/usuarios"
)


def _get_user_or_redirect(id):
    usuario = User.query.get(id)
    if not usuario:
        flash("Usuario no encontrado", "warning")
        return None
    return usuario


@usuarios_bp.route("/")
def listar():
    """Listar todos los usuarios"""
    usuarios = User.query.order_by(User.username).all()
    return render_template(
        "usuarios/list.html",
        usuarios=usuarios
    )


@usuarios_bp.route("/crear", methods=["GET", "POST"])
def crear():
    """Crear nuevo usuario"""
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            email = request.form.get("email", "").strip().lower()
            rol = request.form.get("rol", "auxiliar")
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")
            is_active = request.form.get("is_active") == "on"

            if not username or not email or not password:
                flash("Complete todos los campos obligatorios.", "warning")
                return redirect(url_for("usuarios.crear"))

            if password != confirm_password:
                flash("Las contraseñas no coinciden.", "warning")
                return redirect(url_for("usuarios.crear"))

            if rol not in User.ROLES:
                rol = "auxiliar"

            if User.query.filter_by(username=username).first():
                flash("El nombre de usuario ya existe.", "warning")
                return redirect(url_for("usuarios.crear"))

            if User.query.filter_by(email=email).first():
                flash("El correo electrónico ya está registrado.", "warning")
                return redirect(url_for("usuarios.crear"))

            nuevo_usuario = User(
                username=username,
                email=email,
                rol=rol,
                is_active=is_active
            )
            nuevo_usuario.set_password(password)

            db.session.add(nuevo_usuario)
            db.session.commit()

            flash(f"Usuario {username} creado correctamente", "success")
            return redirect(url_for("usuarios.listar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear usuario: {str(e)}", "danger")
            return redirect(url_for("usuarios.crear"))

    return render_template("usuarios/crear.html")


@usuarios_bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    """Editar usuario"""
    usuario = _get_user_or_redirect(id)
    if not usuario:
        return redirect(url_for("usuarios.listar"))

    if request.method == "POST":
        try:
            email = request.form.get("email", "").strip().lower()
            rol = request.form.get("rol", usuario.rol)

            if not email:
                flash("El correo electrónico es obligatorio.", "warning")
                return redirect(url_for("usuarios.editar", id=id))

            if email != usuario.email:
                existente = User.query.filter_by(email=email).first()
                if existente:
                    flash("El correo electrónico ya está en uso.", "warning")
                    return redirect(url_for("usuarios.editar", id=id))

            if rol not in User.ROLES:
                rol = usuario.rol

            usuario.email = email
            usuario.rol = rol

            db.session.commit()

            flash(f"Usuario {usuario.username} actualizado correctamente", "success")
            return redirect(url_for("usuarios.listar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al actualizar usuario: {str(e)}", "danger")

    return render_template("usuarios/editar.html", usuario=usuario)


@usuarios_bp.route("/<int:id>/cambiar-password", methods=["GET", "POST"])
def cambiar_password(id):
    """Cambiar contraseña del usuario"""
    usuario = _get_user_or_redirect(id)
    if not usuario:
        return redirect(url_for("usuarios.listar"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not password:
            flash("Ingrese una contraseña válida.", "warning")
            return redirect(url_for("usuarios.cambiar_password", id=id))

        if password != confirm_password:
            flash("Las contraseñas no coinciden.", "warning")
            return redirect(url_for("usuarios.cambiar_password", id=id))

        try:
            usuario.set_password(password)
            db.session.commit()
            flash("Contraseña actualizada correctamente.", "success")
            return redirect(url_for("usuarios.listar"))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al cambiar la contraseña: {str(e)}", "danger")

    return render_template(
        "usuarios/cambiar_password.html",
        usuario=usuario
    )


@usuarios_bp.route("/<int:id>/toggle-estado", methods=["POST"])
def toggle_estado(id):
    """Activar o inactivar usuario"""
    usuario = _get_user_or_redirect(id)
    if not usuario:
        return redirect(url_for("usuarios.listar"))

    try:
        usuario.is_active = not usuario.is_active
        db.session.commit()
        estado = "activado" if usuario.is_active else "inactivado"
        flash(f"Usuario {usuario.username} {estado} correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar estado del usuario: {str(e)}", "danger")

    return redirect(url_for("usuarios.listar"))


@usuarios_bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    """Eliminar usuario"""
    usuario = _get_user_or_redirect(id)
    if not usuario:
        return redirect(url_for("usuarios.listar"))

    try:
        db.session.delete(usuario)
        db.session.commit()
        flash(f"Usuario {usuario.username} eliminado correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al eliminar usuario: {str(e)}", "danger")

    return redirect(url_for("usuarios.listar"))
