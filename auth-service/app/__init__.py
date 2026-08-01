from flask import Flask

from app.config import Config
from app.extensions import db, jwt
from app.routes import auth_bp
from app.seed import seed_director


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    jwt.init_app(app)

    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()
        seed_director()

    return app
