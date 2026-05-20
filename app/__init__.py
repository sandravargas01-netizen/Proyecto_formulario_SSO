from flask import Flask
from flask_login import LoginManager
from app.config import config
from app.models import db

login_manager = LoginManager()

def create_app(config_name='development'):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config.get(config_name, config['default']))

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión'

    # Import models and routes AFTER db is initialized
    from app.models.user import User
    from app.models.paciente import Paciente
    from app.routes import register_blueprints

    # Register user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    register_blueprints(app)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
