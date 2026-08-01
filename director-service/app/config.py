import os


class Config:
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/fund")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "change-me")
