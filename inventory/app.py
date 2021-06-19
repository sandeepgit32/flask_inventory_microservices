from flask import Flask

from db import db
from ma import ma

def create_app(config_name='development'):
    app = Flask(__name__)

    if config_name == 'development':
        app.config.from_object('config.DevConfig')
    elif config_name == 'production':
        app.config.from_object('config.ProdConfig')

    db.init_app(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()
    
    return app
