from sqlalchemy import inspect, text

from app import create_app, db

from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen

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

if __name__ == "__main__":
    app.run(debug=True, port=5001)

    
    