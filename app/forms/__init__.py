from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():

    app = Flask(__name__)

    from app.config import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

    db.init_app(app)

    # ==========================
    # IMPORTAR BLUEPRINTS
    # ==========================
    from app.routes.auth_routes import auth_bp
    from app.routes.empleado_routes import empleado_bp
    from app.routes.admin_routes import admin_bp

    # ==========================
    # REGISTRAR BLUEPRINTS
    # ==========================
    app.register_blueprint(auth_bp)
    app.register_blueprint(empleado_bp)
    app.register_blueprint(admin_bp)

    @app.route("/")
    def home():
        return redirect("/empleados/")

    return app