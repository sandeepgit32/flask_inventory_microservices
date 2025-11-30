import os
from dotenv import load_dotenv
# basedir = path.abspath(path.dirname(__file__))
# load_dotenv(path.join(basedir, '.env'))

load_dotenv(".env", verbose=True)

# MySQL connection components
MYSQL_USER = os.environ.get("MYSQL_USER", "admin")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "123456")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = os.environ.get("MYSQL_PORT", "3306")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "catalog_db")


def get_database_uri(env_suffix):
    """Generate database URI with environment-specific database name."""
    db_name = f"{MYSQL_DATABASE}{env_suffix}"
    return f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{db_name}"


class Config:
    """Base config."""

    SECRET_KEY = os.environ.get("APP_SECRET_KEY")
    STATIC_FOLDER = "static"
    TEMPLATES_FOLDER = "templates"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PROPAGATE_EXCEPTIONS = True
    JWT_BLACKLIST_ENABLED = True  # enable blacklist feature
    JWT_BLACKLIST_TOKEN_CHECKS = [
        "access",
        "refresh",
    ]  # allow blacklisting for access and refresh tokens
    MAX_CONTENT_PATH = 10 * 1024 * 1024  # restrict max upload image size to 10MB
    # SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME')
    SQLALCHEMY_ECHO = True


class DevConfig(Config):
    FLASK_ENV = "dev"
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = get_database_uri("_dev")


class TestConfig(Config):
    FLASK_ENV = "test"
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = get_database_uri("_test")


class ProdConfig(Config):
    FLASK_ENV = "prod"
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = get_database_uri("_prod")
