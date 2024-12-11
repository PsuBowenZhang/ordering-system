from flask import Flask
from flask_login import LoginManager
from .auth import auth_bp
from .customer import customer_bp
from .index import index_bp
from .manager import manager_bp
from .models import User

login_manager = LoginManager()
login_manager.login_view = 'index.login'

@login_manager.user_loader
def load_user(user_id):
    """Load a user by their ID."""
    return User.get_user_by_id(user_id)

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder = "../static")
    app.config.from_object('config')

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(manager_bp, url_prefix='/manager')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(index_bp)

    login_manager.init_app(app)
    return app