from flask import Flask

from app.config import Config
from app.extensions import create_mongo_client, create_redis_client, jwt
from app.routes import employee_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    jwt.init_app(app)

    app.mongo_client = create_mongo_client(app)
    app.db = app.mongo_client.get_default_database()
    app.redis = create_redis_client(app)

    app.register_blueprint(employee_bp)

    return app
