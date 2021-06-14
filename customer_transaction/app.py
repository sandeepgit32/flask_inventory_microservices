from flask import Flask, jsonify
from flask_restful import Api
from marshmallow import ValidationError

from resources.transaction import TransactionList, TransactionListByProduct, TransactionListByCustomer, TransactionListByProductAndCustomer

from db import db
from ma import ma

app = Flask(__name__)

# # Using a production configuration
# app.config.from_object('config.ProdConfig')

# Using a development configuration
app.config.from_object('config.DevConfig')

api = Api(app)


@app.before_first_request
def create_tables():
    db.create_all()


@app.errorhandler(ValidationError)
def handle_marshmallow_validation(err):
    return jsonify(err.messages), 400


# customer transaction endpoints
api.add_resource(TransactionList, "/customertransactions")
api.add_resource(TransactionListByProduct, "/customertransactions/product/<string:product_code>")
api.add_resource(TransactionListByCustomer, "/customertransactions/customer/<string:customer_name>")
api.add_resource(TransactionListByProductAndCustomer, "/customertransactions/<string:product_code>/<string:customer_name>")


if __name__ == "__main__":
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)