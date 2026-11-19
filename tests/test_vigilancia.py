import io
import re
import unittest

from flask import Flask
from sqlalchemy import create_engine, inspect, text

from app import create_app, db
from app.models.maestros.cargo import Cargo
from app.models.maestros.dependencia import Dependencia
from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.programa_vigilancia import ProgramaVigilancia
from app.models.transaccionales.user import User
from app.routes.vigilancia_routes import MAX_PDF_BYTES, PROGRAMAS, vigilancia_bp
from app.services.vigilancia_service import actualizar_esquema_vigilancia


class VigilanciaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app()
        cls.app = Flask("app")
        cls.app.config.update(
            TESTING=True, SECRET_KEY="test-secret",
            SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
        db.init_app(cls.app)
        cls.app.register_blueprint(vigilancia_bp)
        cls.app.add_url_rule("/login", endpoint="auth.login", view_func=lambda: "login")
        cls.app.add_url_rule(
            "/empleados/<int:id>", endpoint="empleado.consulta_integral",
            view_func=lambda id: str(id),
        )

    def setUp(self):
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        db.session.add_all([
            User(username="admin", email="admin@example.test", rol="admin", is_active=True),
            User(username="medico", email="medico@example.test", rol="medico", is_active=True),
            Empleado(
                id_empleado=1, cedula="123", nombres="Nombre", apellidos="Prueba",
                cargo=Cargo(nombre="Profesional"), dependencia=Dependencia(nombre="Salud"),
            ),
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def login(self, username="admin", role="admin"):
        with self.client.session_transaction() as state:
            state["usuario"] = username
            state["rol"] = role

    def form(self, program="auditivo"):
        return f"/vigilancia/empleados/1/{program}/nuevo"

    def csrf(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        match = re.search(rb'name="csrf_token" value="([^"]+)"', response.data)
        self.assertIsNotNone(match)
        return match.group(1).decode()

    def values(self, token):
        return {
            "csrf_token": token,
            "fecha_ingreso": "2026-01-02",
            "riesgos": "Ruido",
            "hallazgos": "Hallazgo de prueba",
            "observaciones": "Observación de prueba",
            "descripcion_soporte": "Referencia médica",
            "responsable": "Responsable de prueba",
            "nombre_registrador": "Persona que diligencia",
            "dependencia": "Salud",
            "cargo": "Profesional",
        }

    def test_program_selection_and_each_form(self):
        self.login()
        page = self.client.get("/vigilancia/empleados/1")
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.headers["Cache-Control"], "no-store")
        self.assertIn("Programa de Vigilancia Epidemiológica".encode(), page.data)
        self.assertNotIn(b">Programas de vigilancia</h2>", page.data)
        for code, label in PROGRAMAS.items():
            self.assertIn(label.encode(), page.data)
            form = self.client.get(self.form(code))
            self.assertEqual(form.status_code, 200)
            self.assertIn(b'name="dependencia"', form.data)
            self.assertIn(b'value="Salud"', form.data)
            self.assertIn(b'name="cargo"', form.data)
            self.assertIn(b'value="Profesional"', form.data)
            self.assertIn(b'name="observaciones"', form.data)
            self.assertIn(b'name="nombre_registrador"', form.data)
        self.assertEqual(self.client.get(self.form("desconocido")).status_code, 404)
        self.assertEqual(self.client.get("/vigilancia/empleados/999").status_code, 404)

    def test_save_and_download_pdf_for_employee(self):
        self.login()
        data = self.values(self.csrf(self.form()))
        pdf = b"%PDF-1.4\ncontenido de prueba\n%%EOF"
        data["soporte_pdf"] = (io.BytesIO(pdf), "soporte.pdf")
        response = self.client.post(self.form(), data=data)
        self.assertEqual(response.status_code, 302)
        registro = ProgramaVigilancia.query.one()
        self.assertEqual((registro.id_empleado, registro.programa, registro.riesgos), (1, "auditivo", "Ruido"))
        self.assertEqual(registro.responsable, "Responsable de prueba")
        self.assertEqual(registro.nombre_registrador, "Persona que diligencia")
        self.assertEqual((registro.dependencia, registro.cargo), ("Salud", "Profesional"))
        self.assertEqual(registro.observaciones, "Observación de prueba")
        self.assertEqual(registro.soporte_pdf, pdf)
        self.assertEqual(registro.id_usuario_registro, User.query.filter_by(username="admin").one().id)
        listing = self.client.get("/vigilancia/empleados/1")
        self.assertIn(b"Hallazgo de prueba", listing.data)
        self.assertIn(b"Profesional", listing.data)
        self.assertIn(b"Salud", listing.data)
        self.assertIn(b"Persona que diligencia", listing.data)
        self.assertIn("Observación de prueba".encode(), listing.data)
        download = self.client.get(f"/vigilancia/soportes/{registro.id}")
        self.assertEqual(download.data, pdf)
        self.assertIn("attachment", download.headers["Content-Disposition"])
        self.assertEqual(download.headers["X-Content-Type-Options"], "nosniff")

    def test_admin_only_for_forms_and_documents(self):
        self.assertEqual(self.client.get("/vigilancia/empleados/1").status_code, 302)
        self.login("medico", "medico")
        self.assertEqual(self.client.get("/vigilancia/empleados/1").status_code, 403)
        self.assertEqual(self.client.get(self.form()).status_code, 403)
        self.assertEqual(self.client.get("/vigilancia/soportes/1").status_code, 403)
        self.login("medico", "admin")
        self.assertEqual(self.client.get("/vigilancia/empleados/1").status_code, 403)
        self.login()
        user = User.query.filter_by(username="admin").one()
        user.is_active = False
        db.session.commit()
        self.assertEqual(self.client.get("/vigilancia/empleados/1").status_code, 403)

    def test_validation_preserves_inputs_and_rejects_bad_files_or_csrf(self):
        self.login()
        data = self.values(self.csrf(self.form("quimico")))
        data["fecha_ingreso"] = "2026-02-31"
        data["soporte_pdf"] = (io.BytesIO(b"no es pdf"), "soporte.pdf")
        response = self.client.post(self.form("quimico"), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"fecha de ingreso", response.data)
        self.assertIn(b"no es un PDF", response.data)
        self.assertIn(b"Hallazgo de prueba", response.data)
        self.assertIn("Observación de prueba".encode(), response.data)
        self.assertIn(b'value="Persona que diligencia"', response.data)
        self.assertEqual(ProgramaVigilancia.query.count(), 0)
        data = self.values("invalid-token")
        self.assertEqual(self.client.post(self.form(), data=data).status_code, 400)
        self.assertEqual(ProgramaVigilancia.query.count(), 0)

    def test_optional_support_and_size_limit(self):
        self.login()
        data = self.values(self.csrf(self.form("biologico")))
        response = self.client.post(self.form("biologico"), data=data)
        self.assertEqual(response.status_code, 302)
        registro = ProgramaVigilancia.query.one()
        self.assertIsNone(registro.soporte_pdf)
        self.assertEqual(self.client.get(f"/vigilancia/soportes/{registro.id}").status_code, 404)
        data = self.values(self.csrf(self.form()))
        data["soporte_pdf"] = (io.BytesIO(b"%PDF-" + b"x" * MAX_PDF_BYTES), "grande.pdf")
        response = self.client.post(self.form(), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"5 MB", response.data)
        self.assertEqual(ProgramaVigilancia.query.count(), 1)

    def test_editable_fields_are_optional_and_validation_retains_them(self):
        self.login()
        data = self.values(self.csrf(self.form()))
        data.update(dependencia="Otra dependencia", cargo="Otro cargo", fecha_ingreso="invalida")
        response = self.client.post(self.form(), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'value="Otra dependencia"', response.data)
        self.assertIn(b'value="Otro cargo"', response.data)
        data = self.values(self.csrf(self.form()))
        data.update(dependencia="", cargo="")
        self.assertEqual(self.client.post(self.form(), data=data).status_code, 302)
        registro = ProgramaVigilancia.query.one()
        self.assertIsNone(registro.dependencia)
        self.assertIsNone(registro.cargo)
        listing = self.client.get("/vigilancia/empleados/1")
        self.assertIn(b"No registrada", listing.data)
        self.assertIn(b"No registrado", listing.data)

    def test_observations_are_optional_and_length_is_validated(self):
        self.login()
        data = self.values(self.csrf(self.form()))
        data["observaciones"] = "x" * 10001
        response = self.client.post(self.form(), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"10.000 caracteres", response.data)
        self.assertEqual(ProgramaVigilancia.query.count(), 0)
        data["observaciones"] = ""
        self.assertEqual(self.client.post(self.form(), data=data).status_code, 302)
        self.assertIsNone(ProgramaVigilancia.query.one().observaciones)
        self.assertIn(b"No registradas", self.client.get("/vigilancia/empleados/1").data)

    def test_registrador_is_optional_and_length_is_validated(self):
        self.login()
        data = self.values(self.csrf(self.form()))
        data["nombre_registrador"] = "x" * 201
        response = self.client.post(self.form(), data=data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(b"nombre de quien diligencia", response.data)
        self.assertEqual(ProgramaVigilancia.query.count(), 0)
        data["nombre_registrador"] = ""
        self.assertEqual(self.client.post(self.form(), data=data).status_code, 302)
        self.assertIsNone(ProgramaVigilancia.query.one().nombre_registrador)


class VigilanciaSchemaTests(unittest.TestCase):
    def test_existing_records_survive_idempotent_schema_update(self):
        engine = create_engine("sqlite:///:memory:")
        try:
            with engine.begin() as connection:
                connection.execute(text(
                    "CREATE TABLE programa_vigilancia (id INTEGER PRIMARY KEY, responsable VARCHAR(200))"
                ))
                connection.execute(text(
                    "INSERT INTO programa_vigilancia (id, responsable) VALUES (1, 'Prueba')"
                ))
            actualizar_esquema_vigilancia(engine)
            actualizar_esquema_vigilancia(engine)
            self.assertTrue({"dependencia", "cargo", "observaciones", "nombre_registrador"}.issubset(
                {column["name"] for column in inspect(engine).get_columns("programa_vigilancia")}
            ))
            with engine.connect() as connection:
                row = connection.execute(text(
                    "SELECT responsable, dependencia, cargo, observaciones, nombre_registrador FROM programa_vigilancia WHERE id = 1"
                )).one()
            self.assertEqual(tuple(row), ("Prueba", None, None, None, None))
        finally:
            engine.dispose()


if __name__ == "__main__":
    unittest.main()
