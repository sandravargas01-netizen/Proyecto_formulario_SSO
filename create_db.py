from app import create_app, db

from app.models.transaccionales.user import User
from app.models.transaccionales.examen import Examen
from app.models.transaccionales.empleado import Empleado


app = create_app()

with app.app_context():

    db.drop_all()

    db.create_all()

    if not User.query.filter_by(email="admin@gmail.com").first():
        admin = User(
            username="admin",
            email="admin@gmail.com",
            rol="admin",
            is_active=True
        )
        admin.set_password("123")
        db.session.add(admin)

    if not User.query.filter_by(email="auxiliar@gmail.com").first():
        auxiliar = User(
            username="auxiliar",
            email="auxiliar@gmail.com",
            rol="auxiliar",
            is_active=True
        )
        auxiliar.set_password("123")
        db.session.add(auxiliar)

    db.session.commit()

    print("Base de datos creada correctamente")