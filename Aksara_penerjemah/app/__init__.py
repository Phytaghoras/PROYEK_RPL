from flask import Flask
from flask_migrate import Migrate
from .config import Config
from .models import db, Pengguna
from flask_login import LoginManager
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .admin_views import admin_bp
from .validator_views import validator_bp
from .kontributor_views import kontributor_bp
from .main_views import main

migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inisialisasi database
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Konfigurasi login manager
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    # Register blueprint
    app.register_blueprint(main)
    app.register_blueprint(admin_bp)
    app.register_blueprint(validator_bp)
    app.register_blueprint(kontributor_bp)

    # Membuat tabel di database jika belum ada
    with app.app_context():
        db.create_all()

    @login_manager.user_loader
    def load_user(user_id):
        return Pengguna.query.get(int(user_id))

    return app