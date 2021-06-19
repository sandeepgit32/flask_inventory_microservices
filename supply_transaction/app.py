from flask import Flask, jsonify
from flask_restful import Api
from marshmallow import ValidationError

from resources.transaction import TransactionList, TransactionListByProduct, TransactionListBySupplier, TransactionListByProductAndSupplier

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


# supply transaction endpoints
api.add_resource(TransactionList, "/supplytransactions")
api.add_resource(TransactionListByProduct, "/supplytransactions/product/<string:product_code>")
api.add_resource(TransactionListBySupplier, "/supplytransactions/supplier/<string:supplier_name>")
api.add_resource(TransactionListByProductAndSupplier, "/supplytransactions/product_suplier/<string:product_code>/<string:supplier_name>")


if __name__ == "__main__":
    db.init_app(app)
    ma.init_app(app)
    app.run(port=5000, debug=True)