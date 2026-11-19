import io
import unittest

from flask import Flask
from openpyxl import load_workbook

from app import create_app, db
from app.models.transaccionales.empleado import Empleado
from app.models.transaccionales.examen import Examen
from app.models.transaccionales.user import User
from app.routes.reportes_routes import reportes_bp


class ReportesExcelTests(unittest.TestCase):
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
        cls.app.register_blueprint(reportes_bp)
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
            User(username="auxiliar", email="aux@example.test", rol="auxiliar", is_active=True),
            Empleado(id_empleado=1, cedula="00123", nombres="=1+1", apellidos="Activo",
                     estado="Activo", correo="prueba@example.test"),
            Empleado(id_empleado=2, cedula="456", nombres="Otro", apellidos="Activo",
                     estado="activo"),
            Empleado(id_empleado=3, cedula="789", nombres="Retirado", apellidos="Prueba",
                     estado="Retirado"),
            Examen(id_empleado=1, tipo_examen="ingreso"),
            Examen(id_empleado=1, tipo_examen="periodico"),
            Examen(id_empleado=3, tipo_examen="egreso"),
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def login(self):
        with self.client.session_transaction() as state:
            state["usuario"] = "auxiliar"
            state["rol"] = "auxiliar"

    def test_download_active_employees_and_exam_counts(self):
        self.login()
        response = self.client.get("/reportes/empleados/excel")
        self.assertEqual(response.status_code, 200)
        self.assertIn("empleados_activos.xlsx", response.headers["Content-Disposition"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        sheet = load_workbook(io.BytesIO(response.data)).active
        rows = list(sheet.values)
        self.assertEqual(rows[0], ("Cédula", "Nombres", "Apellidos", "Estado", "Correo", "Total de exámenes"))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1], ("00123", "=1+1", "Activo", "Activo", "prueba@example.test", 2))
        self.assertEqual(sheet["B2"].data_type, "s")
        self.assertEqual(rows[2][0], "456")
        self.assertEqual(rows[2][-1], 0)

    def test_download_requires_active_user(self):
        self.assertEqual(self.client.get("/reportes/empleados/excel").status_code, 302)
        self.login()
        with self.client.session_transaction() as state:
            state["rol"] = "admin"
        self.assertEqual(self.client.get("/reportes/empleados/excel").status_code, 403)
        self.login()
        user = User.query.filter_by(username="auxiliar").one()
        user.is_active = False
        db.session.commit()
        self.assertEqual(self.client.get("/reportes/empleados/excel").status_code, 403)

    def test_empty_export_contains_headers(self):
        self.login()
        Empleado.query.update({Empleado.estado: "Retirado"})
        db.session.commit()
        response = self.client.get("/reportes/empleados/excel")
        self.assertEqual(response.status_code, 200)
        sheet = load_workbook(io.BytesIO(response.data)).active
        self.assertEqual(sheet.max_row, 1)
        self.assertEqual(sheet["F1"].value, "Total de exámenes")

    def test_report_page_and_active_count_match_export(self):
        self.login()
        page = self.client.get("/reportes/empleados?estado=activo")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"Empleados encontrados: 2", page.data)
        self.assertIn(b"/reportes/empleados/excel", page.data)
        self.assertNotIn(b"Retirado", page.data)
        overview = self.client.get("/reportes/")
        self.assertEqual(overview.status_code, 200)
        self.assertIn(b'<h4 class="text-info mb-2">2</h4>', overview.data)


if __name__ == "__main__":
    unittest.main()
