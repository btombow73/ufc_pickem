from flask import Flask
from config import Config
from .extensions import db, login_manager
from .models import User

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Login manager config
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    from .routes import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .admin import admin as admin_blueprint

    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    return app
