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

with app.app_context():

    db.create_all()
    _ensure_examenes_schema()

if __name__ == "__main__":

    app.run(debug=True)