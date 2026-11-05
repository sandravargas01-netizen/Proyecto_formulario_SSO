import os

import click
from sqlalchemy import inspect, text

from app import create_app, db

from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen
from app.models.transaccionales.user import User

app = create_app()


def _ensure_examenes_schema():

    inspector = inspect(db.engine)
    if "examenes" not in inspector.get_table_names():
        return

    existing_columns = [column["name"] for column in inspector.get_columns("examenes")]
    if "fecha_registro" not in existing_columns:
        with db.engine.begin() as conn:
            conn.execute(text("ALTER TABLE examenes ADD COLUMN fecha_registro DATE"))


def _ensure_empleados_schema():

    inspector = inspect(db.engine)
    if "empleados" not in inspector.get_table_names():
        return

    existing_columns = [column["name"] for column in inspector.get_columns("empleados")]
    columns = {
        "ciudad_nacimiento": "VARCHAR(120)",
        "ciudad_residencia": "VARCHAR(120)",
        "escolaridad": "VARCHAR(80)",
        "estado_civil": "VARCHAR(40)",
        "direccion": "VARCHAR(200)",
        "arl": "VARCHAR(120)",
    }

    with db.engine.begin() as conn:
        for name, definition in columns.items():
            if name not in existing_columns:
                conn.execute(text(f"ALTER TABLE empleados ADD COLUMN {name} {definition}"))

with app.app_context():

    db.create_all()
    _ensure_examenes_schema()
    _ensure_empleados_schema()

    bootstrap_admin_password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    if bootstrap_admin_password:
        if len(bootstrap_admin_password) < 12:
            raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD debe tener al menos 12 caracteres")

        bootstrap_admin = User.query.filter_by(email="admin@gmail.com").first()
        if bootstrap_admin is None:
            username_taken = User.query.filter_by(username="admin").first()
            if username_taken:
                raise RuntimeError("El nombre de usuario 'admin' ya está ocupado")
            bootstrap_admin = User(
                username="admin",
                email="admin@gmail.com",
                rol="admin",
                is_active=True
            )
            db.session.add(bootstrap_admin)

        bootstrap_admin.rol = "admin"
        bootstrap_admin.is_active = True
        bootstrap_admin.set_password(bootstrap_admin_password)
        db.session.commit()


@app.cli.command("create-admin")
@click.option("--email", prompt=True)
@click.option("--username", prompt=True)
@click.password_option(confirmation_prompt=True)
def create_admin(email, username, password):
    email = email.strip().lower()
    username = username.strip()

    existing_user = User.query.filter(
        (User.email == email) | (User.username == username)
    ).first()
    if existing_user:
        raise click.ClickException("El correo o nombre de usuario ya está registrado.")

    admin = User(
        username=username,
        email=email,
        rol="admin",
        is_active=True
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo("Administrador creado. Inicia sesión con el correo y la contraseña definidos.")

if __name__ == "__main__":
    app.run(debug=True, port=5001)

    
    