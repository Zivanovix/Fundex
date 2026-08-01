from flask_jwt_extended import JWTManager
from pymongo import MongoClient
from redis import Redis

jwt = JWTManager()


def create_mongo_client(app):
    return MongoClient(app.config["MONGO_URI"])


def create_redis_client(app):
    return Redis.from_url(app.config["REDIS_URL"], decode_responses=True)
