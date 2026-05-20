from flask import Flask, redirect
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():

    app = Flask(__name__)

    app.config.from_object("config.Config")

    db.init_app(app)

    # ==========================================
    # BLUEPRINTS
    # ==========================================

    from app.routes.auth_routes import auth_bp
    from app.routes.paciente_routes import paciente_bp
    from app.routes.admin_routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(paciente_bp)
    app.register_blueprint(admin_bp)

    # ==========================================
    # HOME
    # ==========================================

    @app.route("/")
    def home():
        return redirect("/pacientes/")

    return app