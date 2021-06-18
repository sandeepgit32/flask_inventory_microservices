import os
from dotenv import load_dotenv
# basedir = path.abspath(path.dirname(__file__))
# load_dotenv(path.join(basedir, '.env'))

load_dotenv('.env', verbose=True)


class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('APP_SECRET_KEY')
    STATIC_FOLDER = 'static'
    TEMPLATES_FOLDER = 'templates'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True
    JWT_BLACKLIST_ENABLED = True  # enable blacklist feature
    JWT_BLACKLIST_TOKEN_CHECKS = [
        "access",
        "refresh",
    ] # allow blacklisting for access and refresh tokens
    MAX_CONTENT_PATH = 10 * 1024 * 1024  # restrict max upload image size to 10MB
    # SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')
    SQLALCHEMY_ECHO = True


class ProdConfig(Config):
    FLASK_ENV = 'production'
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('PROD_DATABASE_URI')


class DevConfig(Config):
    FLASK_ENV = 'development'
    DEBUG = True
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')