from flask import Flask

from app.config import Config
from app.extensions import create_mongo_client, create_redis_client, create_web3_client, jwt
from app.listener import start_listener
from app.routes import director_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    jwt.init_app(app)

    app.mongo_client = create_mongo_client(app)
    app.db = app.mongo_client.get_default_database()
    app.redis = create_redis_client(app)
    app.web3 = create_web3_client(app) if app.config["BLOCKCHAIN_ENABLED"] else None

    app.register_blueprint(director_bp)

    if app.config["BLOCKCHAIN_ENABLED"]:
        start_listener(app.db, app.redis, app.web3)

    return app
