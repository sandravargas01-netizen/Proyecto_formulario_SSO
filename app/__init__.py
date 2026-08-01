import os

from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy

from app.config import DevelopmentConfig

db = SQLAlchemy()


def create_app():

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(DevelopmentConfig)

    # ==========================================
    # DATABASE
    # ==========================================

    db.init_app(app)

    # ==========================================
    # BLUEPRINTS
    # ==========================================

    from app.routes.auth_routes import auth_bp
    from app.routes.empleado_routes import empleado_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.examen_routes import examen_bp
    from app.routes.reportes_routes import reportes_bp
    from app.routes.configuracion_routes import configuracion_bp
    from app.routes.usuarios_routes import usuarios_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(empleado_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(examen_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(configuracion_bp)
    app.register_blueprint(usuarios_bp)

    # ==========================================
    # HOME
    # ==========================================

    @app.route("/")
    def home():

        return redirect("/auth/login")

    return app