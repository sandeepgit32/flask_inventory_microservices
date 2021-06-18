from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

api = Api()

def create_app(config_name):
    app = Flask(__name__)

    # Using a development configuration
    if config_name == 'development':
        app.config.from_object('config.DevConfig')
    # Using a development configuration
    elif config_name == 'production':
        app.config.from_object('config.ProdConfig')

    from resources.transaction import TransactionList, TransactionListByProduct, TransactionListByCustomer, TransactionListByProductAndCustomer
    # customer transaction endpoints
    api.add_resource(TransactionList, "/customertransactions")
    api.add_resource(TransactionListByProduct, "/customertransactions/product/<string:product_code>")
    api.add_resource(TransactionListByCustomer, "/customertransactions/customer/<string:customer_name>")
    api.add_resource(TransactionListByProductAndCustomer, "/customertransactions/<string:product_code>/<string:customer_name>")

    api.init_app(app)
    db.init_app(app)
    ma.init_app(app)

    with app.app_context():
        db.create_all()
    
    return app
