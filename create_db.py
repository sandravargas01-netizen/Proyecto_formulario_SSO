from app import create_app, db

# IMPORTAR MODELOS
from app.models.examen import Examen
from app.models.user import User
from Proyecto_formulario_SSO.app.models.empleados import Paciente

app = create_app()

with app.app_context():

    db.create_all()

    print("Base de datos y tablas creadas correctamente")