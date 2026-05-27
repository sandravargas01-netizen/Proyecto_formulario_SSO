import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = "secretkey"

    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = \
        "sqlite:///" + os.path.join(
            BASE_DIR,
            "salud_ocupacional.db"
        )