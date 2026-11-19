from sqlalchemy import inspect, text


def actualizar_esquema_vigilancia(engine):
    with engine.begin() as connection:
        if connection.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(hashtext('programa_vigilancia_schema'))"))
        elif connection.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        inspector = inspect(connection)
        if not inspector.has_table("programa_vigilancia"):
            return
        columns = {column["name"] for column in inspector.get_columns("programa_vigilancia")}
        for name, definition in (
            ("dependencia", "VARCHAR(200)"),
            ("cargo", "VARCHAR(200)"),
            ("observaciones", "TEXT"),
            ("nombre_registrador", "VARCHAR(200)"),
        ):
            if name not in columns:
                connection.execute(text(f"ALTER TABLE programa_vigilancia ADD COLUMN {name} {definition}"))